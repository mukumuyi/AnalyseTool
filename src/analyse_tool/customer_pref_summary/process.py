"""② データ加工 — 顧客マスタのクレンジング/前処理。

集計に使う `pref` / `segment` / `customer_id` の欠損・重複・表記ゆれ
（前後の空白など）を取り除き、分析ステップにそのまま渡せる状態にする。
"""

from __future__ import annotations

import duckdb


def clean_customers(customers: duckdb.DuckDBPyRelation) -> duckdb.DuckDBPyRelation:
    """pref・segmentが欠損/空文字の行を除外し、customer_idの重複を除く。"""
    return customers.query(
        "customers_raw",
        """
        SELECT DISTINCT ON (customer_id) *
        FROM customers_raw
        WHERE pref IS NOT NULL
          AND segment IS NOT NULL
          AND trim(pref) != ''
          AND trim(segment) != ''
        ORDER BY customer_id
        """,
    )
