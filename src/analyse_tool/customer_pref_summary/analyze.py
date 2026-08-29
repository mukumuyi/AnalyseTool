"""③ 分析 — pref×segmentの件数集計と、可視化用の明細データ抽出。

可視化には集計済みの小さいデータだけを渡す方針に沿い、ここで
「pref×segmentごとの件数」（グラフ用）と「クリック時に表示する明細
（顧客一覧）」の2つの小さいデータフレームを作る。
"""

from __future__ import annotations

import duckdb
import pandas as pd


def aggregate_by_pref_segment(
    customers: duckdb.DuckDBPyRelation,
) -> tuple[pd.DataFrame, list[str], pd.DataFrame]:
    """pref×segmentごとの件数集計、pref別の並び順、明細データを作る。

    Returns:
        agg_df: `pref` / `segment` / `count` の3列。グラフ描画にそのまま渡せる。
        pref_order: 顧客総数が多い順に並べた `pref` のリスト（グラフの横軸順）。
        detail_df: `customer_id` / `customer_name` / `segment` / `pref` の明細。
            クリックした棒（pref×segment）に対応する行だけをブラウザ側のJSで
            絞り込んで表示するために使う。
    """
    agg_df = customers.query(
        "customers_clean",
        """
        SELECT pref, segment, COUNT(*) AS count
        FROM customers_clean
        GROUP BY pref, segment
        """,
    ).df()

    pref_totals = customers.query(
        "customers_clean",
        """
        SELECT pref, COUNT(*) AS total
        FROM customers_clean
        GROUP BY pref
        ORDER BY total DESC
        """,
    ).df()
    pref_order = pref_totals["pref"].tolist()

    detail_df = customers.query(
        "customers_clean",
        """
        SELECT customer_id, customer_name, segment, pref
        FROM customers_clean
        ORDER BY customer_id
        """,
    ).df()

    return agg_df, pref_order, detail_df
