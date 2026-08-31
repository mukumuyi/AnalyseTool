"""② データ加工 — proc_historyのクレンジングと列付与。

数百万行規模の`proc_history`を対象にするため、pandasへ全件ロードせず
DuckDBのリレーション（遅延評価）のまま処理する。
"""

from __future__ import annotations

import duckdb


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
