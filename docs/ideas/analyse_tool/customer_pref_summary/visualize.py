"""④ 可視化 — pref別・segment色分けの棒グラフ + クリック連動の明細レポート。

`common/charts/bar.py`（グラフ生成）と `common/report.py`
（グラフ＋明細表＋クリックJSのレポート組み立て）を組み合わせるだけの層に徹する。
"""

from __future__ import annotations

import pandas as pd

from analyse_tool.common.charts.bar import stacked_bar
from analyse_tool.common.report import build_bar_click_detail_html

REPORT_TITLE = "地方区分(pref)別 顧客数（顧客区分(segment)別内訳）"


def build_report(agg_df: pd.DataFrame, pref_order: list[str], detail_df: pd.DataFrame) -> str:
    """集計データ・明細データからレポートHTML文字列を組み立てる。"""
    fig = stacked_bar(
        agg_df,
        x="pref",
        y="count",
        color="segment",
        x_order=pref_order,
        title=REPORT_TITLE,
        x_title="地方区分(pref)",
        y_title="顧客数",
    )
    return build_bar_click_detail_html(
        fig,
        detail_df,
        detail_match_columns={"x": "pref", "trace_name": "segment"},
        title=REPORT_TITLE,
    )
