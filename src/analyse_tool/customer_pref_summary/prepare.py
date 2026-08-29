"""① 前準備（EDA） — 顧客マスタ(customers)の傾向を把握する。

件数・欠損率・型・カテゴリ分布などをDuckDBで集計し、後続の
データ加工・分析の方針を決めるための材料にする。ここでは加工
（結合・集計・変換）そのものは行わない。
"""

from __future__ import annotations

from analyse_tool.common.profile import DatasetProfile, profile_from_parquet


def profile_customers(input_path: str) -> DatasetProfile:
    """顧客マスタの傾向プロファイル（件数・欠損率・カテゴリ分布など）を作る。"""
    return profile_from_parquet(input_path, name="customers")
