"""② データ加工 — proc_historyのクレンジングと列付与。

数百万行規模の`proc_history`を対象にするため、pandasへ全件ロードせず
DuckDBのリレーション（遅延評価）のまま処理する。

`eqp_workload_analysis`（旧版）の同名モジュールと処理内容は同じだが、
旧版ツールへは一切手を入れない方針のため複製実装している
（`.steering/20260901-eqp-workload-fastview/design.md`の「課題対応」
参照）。
"""

from __future__ import annotations

import duckdb

MATERIALIZED_TABLE_NAME = "proc_history_annotated_materialized"


def clean_proc_history(
    proc_history: duckdb.DuckDBPyRelation,
) -> duckdb.DuckDBPyRelation:
    """集計・分析に使う必須列の欠損行を除外し、型を整形する。"""
    return proc_history.query(
        "proc_history_raw",
        """
        SELECT
            lot_id,
            prodspec_id,
            mainpd_id,
            ope_no,
            CAST(ope_seq AS BIGINT) AS ope_seq,
            eqp_id,
            CAST(start_time AS TIMESTAMP) AS start_time,
            CAST(end_time AS TIMESTAMP) AS end_time
        FROM proc_history_raw
        WHERE lot_id IS NOT NULL
          AND eqp_id IS NOT NULL
          AND ope_seq IS NOT NULL
          AND start_time IS NOT NULL
          AND end_time IS NOT NULL
        """,
    )


def annotate_lot_sequence(
    proc_history: duckdb.DuckDBPyRelation,
) -> duckdb.DuckDBPyRelation:
    """ロットの工程順に、待機時間と前後工程の設備IDを1回のSELECT文で付与する。

    `lot_id`ごとに`ope_seq`順に並べたときの、DuckDBのwindow関数
    （`PARTITION BY lot_id ORDER BY ope_seq`）で次の3列を付与する。
    待機時間の算出と前後工程の付与を別々の2パスにせず、数百万行の
    テーブルを2回スキャンしない。

    - `wait_minutes`: このope_seqの`start_time`から、1つ前のope_seqの
      `end_time`（`LAG(end_time)`）を引いた分数。ロット最初の工程は
      `NULL`になる。
    - `next_eqp_id`: 1つ後のope_seqの`eqp_id`（`LEAD(eqp_id)`）。
      ロット最後の工程は`NULL`になる。
    - `prev_eqp_id`: 1つ前のope_seqの`eqp_id`（`LAG(eqp_id)`）。
      ロット最初の工程は`NULL`になる。
    """
    return proc_history.query(
        "proc_history_clean",
        """
        SELECT
            *,
            date_diff(
                'minute',
                LAG(end_time) OVER (PARTITION BY lot_id ORDER BY ope_seq),
                start_time
            ) AS wait_minutes,
            LEAD(eqp_id) OVER (PARTITION BY lot_id ORDER BY ope_seq) AS next_eqp_id,
            LAG(eqp_id) OVER (PARTITION BY lot_id ORDER BY ope_seq) AS prev_eqp_id
        FROM proc_history_clean
        """,
    )


def materialize(
    con: duckdb.DuckDBPyConnection, annotated: duckdb.DuckDBPyRelation
) -> duckdb.DuckDBPyRelation:
    """`annotated`（LAG/LEADのwindow関数を含む遅延評価のリレーション）を実テーブル化する。

    ⑥-3/⑥-4は対象日ごとに何度も`annotated`へ問い合わせる。遅延評価の
    リレーションのまま問い合わせを重ねると、そのたびに上流（`read_parquet`
    からwindow関数まで）が数百万行規模で再計算されてしまい、日数が増える
    ほど線形に遅くなる（実測: サンプルデータ・上位5設備・10日分で約48秒）。
    1回だけ実テーブルへ書き出すことで、以降の問い合わせを数百倍高速に
    保つ（実測: 同条件で約5秒）。
    """
    con.execute(f"DROP TABLE IF EXISTS {MATERIALIZED_TABLE_NAME}")
    annotated.to_table(MATERIALIZED_TABLE_NAME)
    return con.table(MATERIALIZED_TABLE_NAME)
