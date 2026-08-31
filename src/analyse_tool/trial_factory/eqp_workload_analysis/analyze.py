"""③ 分析 — 設備ごとの稼働負荷集計と、ドリルダウン用の元データ抽出。

`process.py`の出力（数百万行）はここで初めて.df()され、以降は
`EqpWorkloadDF`（約400行）・`HourlyDF`（数百〜数千行）・`LotDetail`
（数千行）という小さいデータフレームだけを扱う。時間帯ごとの集計は
`generate_series`と区間交差のSQL集合演算で行い、ロットごとにPythonで
ループしない。
"""

from __future__ import annotations

import duckdb
import pandas as pd

from analyse_tool.common.charts.pareto import pareto_data

DEFAULT_TOP_N = 15
DEFAULT_PERIOD_DAYS = 3
BUSY = "着工中"
WAIT = "待機"


def aggregate_eqp_workload(annotated: duckdb.DuckDBPyRelation) -> pd.DataFrame:
    """設備ごとの処理数・待機時間（合計・平均）を集計する（`EqpWorkloadDF`）。

    ①〜⑤の元データ。ここで初めて`.df()`し、以降はpandasで扱う
    （設備数は多くても数百件程度のため軽い）。
    """
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
    """`EqpWorkloadDF`を待機時間の多い順に並べ、上位`top_n`件の`ParetoDF`を作る。

    並べ替え・累積構成比の算出そのものは`common/charts/pareto.py`の
    `pareto_data()`（第2層の汎用ロジック）を再利用する。
    """
    return pareto_data(workload_df, category="eqp_id", value=value, top_n=top_n)


def build_hourly_utilization(
    annotated: duckdb.DuckDBPyRelation,
    eqp_ids: list[str],
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
) -> pd.DataFrame:
    """上位設備・代表期間の稼働状況を1時間刻みで集計する（`HourlyDF`）。

    設備×時間帯ごとに「着工中(busy)」「待機(wait)」の分数（0〜60分、
    合計60分になる）を、`generate_series`と区間交差の判定でSQL集合演算
    により求める（ロットごとにPythonで按分しない）。あわせて、その
    時間帯に着工した件数（`start_count`）も求める（折れ線用）。

    Returns:
        `eqp_id`/`hour_start`/`status`（`"着工中"`/`"待機"`）/`minutes`/
        `start_count`の列を持つ縦持ちデータ。`start_count`は同じ
        `eqp_id`×`hour_start`の2行（busy/wait）で同じ値を持つ
        （`barline.bar_with_line()`が`x`ごとに重複排除して折れ線を引く
        ため）。
    """
    if not eqp_ids:
        return pd.DataFrame(
            columns=["eqp_id", "hour_start", "status", "minutes", "start_count"]
        )

    eqp_list_sql = ", ".join(f"'{e}'" for e in eqp_ids)

    result = annotated.query(
        "proc_history_annotated",
        f"""
        WITH target AS (
            SELECT *
            FROM proc_history_annotated
            WHERE eqp_id IN ({eqp_list_sql})
              AND start_time < TIMESTAMP '{period_end}'
              AND end_time > TIMESTAMP '{period_start}'
        ),
        hours AS (
            SELECT eqp_id, hour_start
            FROM (SELECT DISTINCT eqp_id FROM target) e
            CROSS JOIN generate_series(
                TIMESTAMP '{period_start}',
                TIMESTAMP '{period_end}' - INTERVAL 1 HOUR,
                INTERVAL 1 HOUR
            ) AS t(hour_start)
        ),
        overlap AS (
            -- DuckDBのGREATEST/LEASTはNULL引数を無視して残りの引数を返すため、
            -- ここをLEFT JOINにすると「重なる行が無い時間帯」がtarget側NULLの
            -- まま計算され、`GREATEST(hour_start, NULL)=hour_start`
            -- `LEAST(hour_start+1h, NULL)=hour_start+1h`という形で
            -- 満稼働（60分）に化けてしまう。重なる行が実在する組み合わせだけを
            -- 対象にするINNER JOINにし、「該当行なし」は次のGROUP BYで単純に
            -- 存在しない（＝0分）ものとして扱う。
            SELECT
                h.eqp_id,
                h.hour_start,
                GREATEST(
                    0,
                    date_diff(
                        'second',
                        GREATEST(h.hour_start, target.start_time),
                        LEAST(h.hour_start + INTERVAL 1 HOUR, target.end_time)
                    )
                ) / 60.0 AS busy_minutes
            FROM hours h
            JOIN target
              ON target.eqp_id = h.eqp_id
             AND target.start_time < h.hour_start + INTERVAL 1 HOUR
             AND target.end_time > h.hour_start
        ),
        busy_by_hour AS (
            SELECT eqp_id, hour_start, LEAST(60.0, SUM(busy_minutes)) AS busy_minutes
            FROM overlap
            GROUP BY eqp_id, hour_start
        ),
        starts_by_hour AS (
            -- 時間帯の境界は`period_start`起点（分・秒付き）であり、
            -- `date_trunc('hour', ...)`（0分0秒起点）とは一致しないため、
            -- `hours`と同じ半開区間の条件で結合する（`overlap`と同様の方式）。
            SELECT h.eqp_id, h.hour_start, COUNT(target.lot_id) AS start_count
            FROM hours h
            LEFT JOIN target
              ON target.eqp_id = h.eqp_id
             AND target.start_time >= h.hour_start
             AND target.start_time < h.hour_start + INTERVAL 1 HOUR
            GROUP BY h.eqp_id, h.hour_start
        )
        SELECT
            h.eqp_id,
            h.hour_start,
            COALESCE(b.busy_minutes, 0.0) AS busy_minutes,
            COALESCE(s.start_count, 0) AS start_count
        FROM hours h
        LEFT JOIN busy_by_hour b USING (eqp_id, hour_start)
        LEFT JOIN starts_by_hour s USING (eqp_id, hour_start)
        ORDER BY eqp_id, hour_start
        """,
    ).df()

    return _to_busy_wait_long(result)


def _to_busy_wait_long(wide: pd.DataFrame) -> pd.DataFrame:
    """`busy_minutes`列を「着工中／待機」の縦持ち（`status`/`minutes`）に直す。"""
    busy = wide.assign(status=BUSY, minutes=wide["busy_minutes"])
    wait = wide.assign(status=WAIT, minutes=60.0 - wide["busy_minutes"])
    long_df = pd.concat([busy, wait], ignore_index=True)
    return long_df[["eqp_id", "hour_start", "status", "minutes", "start_count"]]


def build_lot_records(
    annotated: duckdb.DuckDBPyRelation,
    eqp_ids: list[str],
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
    boundary_buffer_days: int = 1,
) -> pd.DataFrame:
    """上位設備・代表期間のロット明細を抽出する（`LotDetail`）。

    ⑥-3（ガントチャート＋仕掛数量推移）・⑥-4（ロット明細表）はブラウザ側の
    JSがこのデータから都度組み立てる「構築式」（`common/report.py`参照）
    のため、対象は上位設備の行そのものだけでなく、**前後工程が上位設備の
    行**も含める。「待機中（他装置着工）」（上位設備を出て別の設備へ向かう
    ロット）の待機終了時刻は、その別設備側の行の`start_time`でしか
    分からないため。

    Returns:
        `lot_id`/`prodspec_id`/`mainpd_id`/`ope_no`/`ope_seq`/`eqp_id`/
        `start_time`/`end_time`/`wait_minutes`/`prev_eqp_id`/
        `next_eqp_id`の列を持つ明細行（代表期間の前後`boundary_buffer_days`
        日を含めた範囲）。
    """
    if not eqp_ids:
        return pd.DataFrame(
            columns=[
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
        )

    eqp_list_sql = ", ".join(f"'{e}'" for e in eqp_ids)

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
