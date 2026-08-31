"""① 前準備（EDA） — proc_historyの傾向を把握する。

件数・欠損率・カテゴリ分布などをDuckDBで集計し、後続のデータ加工・
分析の方針を決めるための材料にする。ここでは加工そのものは行わない。
レポートの組み立てには使わない（`customer_pref_summary`と同じ位置づけ）。
"""

from __future__ import annotations

from analyse_tool.common.profile import DatasetProfile, profile_from_parquet


def profile_proc_history(input_path: str) -> DatasetProfile:
    """`proc_history`の傾向プロファイル（件数・欠損率・カテゴリ分布など）を作る。"""
    return profile_from_parquet(input_path, name="proc_history")
