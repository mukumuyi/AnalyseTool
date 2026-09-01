"""① 前準備（EDA） — proc_historyの傾向を把握する。

件数・欠損率・カテゴリ分布などをDuckDBで集計し、後続のデータ加工・
分析の方針を決めるための材料にする。ここでは加工そのものは行わない。

`eqp_workload_analysis`（旧版）の同名モジュールと処理内容は同じだが、
旧版ツールへは一切手を入れない方針のため複製実装している
（`.steering/20260901-eqp-workload-fastview/design.md`の「課題対応」
参照）。
"""

from __future__ import annotations

from analyse_tool.common.profile import DatasetProfile, profile_from_parquet


def profile_proc_history(input_path: str) -> DatasetProfile:
    """`proc_history`の傾向プロファイル（件数・欠損率・カテゴリ分布など）を作る。"""
    return profile_from_parquet(input_path, name="proc_history")
