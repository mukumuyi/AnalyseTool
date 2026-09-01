"""③ 分析 — 設備ごとの稼働負荷集計と、日別ドリルダウン用データの抽出。

①〜⑤・⑥-1（`aggregate_eqp_workload`/`build_pareto`）は`eqp_workload_analysis`
（旧版）と同じ集計内容だが、旧版ツールへ一切手を入れない方針のため複製
実装している（`.steering/20260901-eqp-workload-fastview/design.md`の
「課題対応」参照）。

⑥-2（日次インデックス）・⑥-3/⑥-4（日別のガント・仕掛数量・ロット明細）
は本ツールの新規部分で、旧版の「代表期間まるごと埋め込み」に代えて、
選択した1日分だけを都度取り出せる小さいデータを作る。サブレーン割当
（`assign_sublanes`）だけは、対象が1設備・1日分＝多くても数百区間と
小さいためDuckDBのSQLではなくPythonの純粋関数で行う（ユニットテストの
しやすさを優先する）。
"""

from __future__ import annotations

from collections.abc import Sequence

import duckdb
import pandas as pd

from analyse_tool.common.charts.pareto import pareto_data

DEFAULT_TOP_N = 15
WIP_BUCKET_MINUTES = 15
BOUNDARY_BUFFER_DAYS = 1


def aggregate_eqp_workload(annotated: duckdb.DuckDBPyRelation) -> pd.DataFrame:
    """設備ごとの処理数・待機時間（合計・平均）を集計する（①〜⑤・⑥-1の元データ）。"""
    return annotated.query(
        "proc_history_annotated",
        """
        SELECT
            eqp_id,
            COUNT(*) AS proc_count,
            COALESCE(SUM(wait_minutes), 0) AS wait_total_minutes,
            COALESCE(AVG(wait_minutes), 0) AS wait_avg_minutes
        FROM proc_history_annotated
        GROUP BY eqp_id
        """,
    ).df()


def build_pareto(
    workload_df: pd.DataFrame,
    value: str = "wait_total_minutes",
    top_n: int = DEFAULT_TOP_N,
) -> pd.DataFrame:
    """`workload_df`を待機時間の多い順に並べ、上位`top_n`件のパレート用データを作る。"""
    return pareto_data(workload_df, category="eqp_id", value=value, top_n=top_n)


def _eqp_list_sql(eqp_ids: Sequence[str]) -> str:
    return ", ".join(f"'{e}'" for e in eqp_ids)


def aggregate_daily_index(
    annotated: duckdb.DuckDBPyRelation, eqp_ids: Sequence[str]
) -> pd.DataFrame:
    """対象設備群×日ごとの稼働率・着工件数を集計する（⑥-2用、全期間・小容量）。

    稼働が全く無い日はGROUP BYの結果に現れないため、観測された最小日〜
    最大日の連続した日付で0埋めする（⑥-2の日クリック帯に穴を作らない
    ため）。

    Returns:
        `day`（`date`）/`busy_minutes`/`start_count`/`utilization_pct`
        （対象設備群×24時間に対する稼働時間の割合、0〜100）の列を持つ、
        日付昇順のデータ。
    """
    columns = ["day", "busy_minutes", "start_count", "utilization_pct"]
    if not eqp_ids:
        return pd.DataFrame(columns=columns)

    eqp_list_sql = _eqp_list_sql(eqp_ids)
    result = annotated.query(
        "proc_history_annotated",
        f"""
        SELECT
            CAST(date_trunc('day', start_time) AS DATE) AS day,
            SUM(date_diff('minute', start_time, end_time)) AS busy_minutes,
            COUNT(*) AS start_count
        FROM proc_history_annotated
        WHERE eqp_id IN ({eqp_list_sql})
        GROUP BY 1
        ORDER BY 1
        """,
    ).df()

    if result.empty:
        return pd.DataFrame(columns=columns)

    full_days = pd.date_range(result["day"].min(), result["day"].max(), freq="D")
    filled = (
        result.set_index("day")
        .reindex(full_days)
        .rename_axis("day")
        .fillna(0)
        .reset_index()
    )
    filled["day"] = filled["day"].dt.date
    filled["start_count"] = filled["start_count"].astype("int64")
    minutes_per_day = len(eqp_ids) * 24 * 60
    filled["utilization_pct"] = (filled["busy_minutes"] / minutes_per_day * 100).clip(
        upper=100.0
    )
    return filled[columns]


def build_day_segments(
    annotated: duckdb.DuckDBPyRelation,
    eqp_ids: Sequence[str],
    day_start: pd.Timestamp,
    day_end: pd.Timestamp,
) -> pd.DataFrame:
    """対象設備群・対象日の工程区間を抽出し、当日境界へクリップする（⑥-3用）。

    Returns:
        `eqp_id`/`lot_id`/`start_time`/`end_time`の列を持つ区間データ
        （`start_time`/`end_time`は`[day_start, day_end)`にクリップ済み）。
        サブレーン番号はここでは付与しない（`assign_lanes_to_segments()`参照）。
    """
    columns = ["eqp_id", "lot_id", "start_time", "end_time"]
    if not eqp_ids:
        return pd.DataFrame(columns=columns)

    eqp_list_sql = _eqp_list_sql(eqp_ids)
    return annotated.query(
        "proc_history_annotated",
        f"""
        SELECT
            eqp_id,
            lot_id,
            GREATEST(start_time, TIMESTAMP '{day_start}') AS start_time,
            LEAST(end_time, TIMESTAMP '{day_end}') AS end_time
        FROM proc_history_annotated
        WHERE eqp_id IN ({eqp_list_sql})
          AND start_time < TIMESTAMP '{day_end}'
          AND end_time > TIMESTAMP '{day_start}'
        ORDER BY eqp_id, start_time
        """,
    ).df()


def assign_sublanes(segments: Sequence[tuple[pd.Timestamp, pd.Timestamp]]) -> list[int]:
    """区間のリスト（開始・終了）に、重ならない最小本数のサブレーン番号を割り当てる。

    開始時刻順に、既存レーンのうち直前区間が終了済み（`lane_end <= start`）の
    最小番号を再利用する。空きがなければ新しいレーンを追加する（貪欲法）。
    旧版のブラウザ側JS`greedyPackLanes()`と同じ考え方をPythonへ移植した
    ものだが、対象範囲は「同一設備内」に変わっている（旧版は設備をまたいだ
    「並行処理枠」だった）。

    Args:
        segments: `(start, end)`のタプルのリスト。半開区間`[start, end)`
            として扱う。

    Returns:
        `segments`と同じ順序・同じ長さの、0始まりのレーン番号リスト。
    """
    order = sorted(range(len(segments)), key=lambda i: segments[i][0])
    lane_ends: list[pd.Timestamp] = []
    lanes = [0] * len(segments)
    for i in order:
        start, end = segments[i]
        lane_idx = -1
        for lane, lane_end in enumerate(lane_ends):
            if lane_end <= start:
                lane_idx = lane
                break
        if lane_idx == -1:
            lane_idx = len(lane_ends)
            lane_ends.append(end)
        else:
            lane_ends[lane_idx] = end
        lanes[i] = lane_idx
    return lanes


def assign_lanes_to_segments(segments_df: pd.DataFrame) -> pd.DataFrame:
    """`build_day_segments()`の結果に、設備ごとの`lane`列を付与する。"""
    if segments_df.empty:
        return segments_df.assign(lane=pd.Series(dtype="int64"))

    parts = []
    for eqp_id, sub in segments_df.groupby("eqp_id", sort=False):
        sub = sub.reset_index(drop=True)
        pairs = list(zip(sub["start_time"], sub["end_time"], strict=True))
        parts.append(sub.assign(lane=assign_sublanes(pairs)))
    return pd.concat(parts, ignore_index=True)


def build_day_wip_series(
    annotated: duckdb.DuckDBPyRelation,
    eqp_ids: Sequence[str],
    day_start: pd.Timestamp,
    day_end: pd.Timestamp,
) -> pd.DataFrame:
    """対象設備群・対象日の全仕掛数量推移を15分刻みで求める（⑥-3用）。

    各時点`t`（15分刻み）について、次の2分類それぞれに該当する区間の
    「その時点で進行中の件数」を数える（分単位の面積ではなく瞬間値の
    サンプリング）。待機中は当初「自装置着工待ち」「他装置着工待ち」の
    2区分に分けていたが、ユーザー指示（2026-09-02）により1区分へ統合した
    （経緯は`.steering/20260901-eqp-workload-fastview/design.md`
    「追加設計5」参照）。

    - 着工中: `[start_time, end_time)`
    - 待機中: 次の2種類の待機区間の和（同一ロットの同一待機区間が両方に
      該当することは無い。詳細は追加設計4の二重計上バグ修正を参照）。
      - 対象設備群のいずれかへ着工するまでの待機:
        `[start_time - wait_minutes分, start_time)`
      - 対象設備群のいずれかを出て、対象設備群に含まれない次工程へ
        向かうまでの待機: `[end_time, 次工程のstart_time)`

    対象を日で絞り込んでも待機区間が日をまたぐことがあるため、抽出範囲は
    前後`BOUNDARY_BUFFER_DAYS`日を含める。

    Returns:
        `t`（15分刻みの時刻）/`busy`/`wait`（いずれも件数）の列を持つ
        データ（`day_start`から`day_end`未満、96行）。
    """
    columns = ["t", "busy", "wait"]
    if not eqp_ids:
        return pd.DataFrame(columns=columns)

    eqp_list_sql = _eqp_list_sql(eqp_ids)
    buffer_start = day_start - pd.Timedelta(days=BOUNDARY_BUFFER_DAYS)
    buffer_end = day_end + pd.Timedelta(days=BOUNDARY_BUFFER_DAYS)

    result = annotated.query(
        "proc_history_annotated",
        f"""
        WITH target AS (
            SELECT *
            FROM proc_history_annotated
            WHERE eqp_id IN ({eqp_list_sql})
              AND start_time < TIMESTAMP '{buffer_end}'
              AND end_time > TIMESTAMP '{buffer_start}'
        ),
        next_row AS (
            SELECT
                t.end_time AS wait_departure_start,
                n.start_time AS wait_departure_end
            FROM target t
            JOIN proc_history_annotated n
              ON n.lot_id = t.lot_id AND n.ope_seq = t.ope_seq + 1
            WHERE t.next_eqp_id IS NOT NULL
              AND t.next_eqp_id <> t.eqp_id
              AND t.next_eqp_id NOT IN ({eqp_list_sql})
        ),
        buckets AS (
            SELECT t AS bucket_t
            FROM generate_series(
                TIMESTAMP '{day_start}',
                TIMESTAMP '{day_end}' - INTERVAL 15 MINUTE,
                INTERVAL 15 MINUTE
            ) AS s(t)
        )
        SELECT
            b.bucket_t AS t,
            (
                SELECT COUNT(*) FROM target i
                WHERE i.start_time <= b.bucket_t AND i.end_time > b.bucket_t
            ) AS busy,
            (
                SELECT COUNT(*) FROM target i
                WHERE i.wait_minutes IS NOT NULL AND i.wait_minutes > 0
                  AND i.start_time - (INTERVAL '1 minute' * i.wait_minutes) <= b.bucket_t
                  AND i.start_time > b.bucket_t
            ) + (
                SELECT COUNT(*) FROM next_row i
                WHERE i.wait_departure_start <= b.bucket_t AND i.wait_departure_end > b.bucket_t
            ) AS wait
        FROM buckets b
        ORDER BY b.bucket_t
        """,
    ).df()
    return result[columns]


def build_lot_records(
    annotated: duckdb.DuckDBPyRelation,
    eqp_ids: Sequence[str],
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
    boundary_buffer_days: int = BOUNDARY_BUFFER_DAYS,
) -> pd.DataFrame:
    """対象設備群・対象期間のロット明細を抽出する（⑥-4用）。

    ⑥-3・⑥-4はブラウザ側が日別JSONから都度組み立てるため、対象は
    対象設備群の行そのものだけでなく、**前後工程が対象設備群の行**も
    含める。「待機中（他装置着工）」（対象設備群を出て別の設備へ向かう
    ロット）の待機終了時刻は、その別設備側の行の`start_time`でしか
    分からないため。

    `period_start`/`period_end`に1日分（`day_start`/`day_end`）を渡せば
    ⑥-3の日別データ用に、代表期間を渡せば旧版と同じ使い方ができる
    （旧版`build_lot_records()`と同じ汎用シグネチャ）。

    Returns:
        `lot_id`/`prodspec_id`/`mainpd_id`/`ope_no`/`ope_seq`/`eqp_id`/
        `start_time`/`end_time`/`wait_minutes`/`prev_eqp_id`/
        `next_eqp_id`の列を持つ明細行。
    """
    columns = [
        "lot_id",
        "prodspec_id",
        "mainpd_id",
        "ope_no",
        "ope_seq",
        "eqp_id",
        "start_time",
        "end_time",
        "wait_minutes",
        "prev_eqp_id",
        "next_eqp_id",
    ]
    if not eqp_ids:
        return pd.DataFrame(columns=columns)

    eqp_list_sql = _eqp_list_sql(eqp_ids)

    return annotated.query(
        "proc_history_annotated",
        f"""
        SELECT
            lot_id, prodspec_id, mainpd_id, ope_no, ope_seq, eqp_id,
            start_time, end_time, wait_minutes, prev_eqp_id, next_eqp_id
        FROM proc_history_annotated
        WHERE (
            eqp_id IN ({eqp_list_sql})
            OR prev_eqp_id IN ({eqp_list_sql})
            OR next_eqp_id IN ({eqp_list_sql})
        )
        AND start_time < TIMESTAMP '{period_end}' + INTERVAL '{boundary_buffer_days}' DAY
        AND end_time > TIMESTAMP '{period_start}' - INTERVAL '{boundary_buffer_days}' DAY
        ORDER BY lot_id, ope_seq
        """,
    ).df()
