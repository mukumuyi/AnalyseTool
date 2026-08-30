"""円グラフを組み立てる共通モジュール。

カテゴリ列の構成比を確認する用途を主に想定（EDAでの分布把握、可視化
レポートでの内訳表示のどちらにも使う）。件数・金額の集計は事前に
`analyze.py`側で済ませ、集計済みの小さいデータを渡す。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def pie(
    df: pd.DataFrame,
    names: str,
    values: str,
    title: str | None = None,
    hole: float = 0.0,
) -> go.Figure:
    """カテゴリ列 `names` の構成比を円グラフで表す。

    Args:
        df: 集計済みデータ（`names`ごとに1行、`values`に件数・金額等）。
        names: カテゴリ列名（凡例・ラベルに使う）。
        values: 値の列名（円の面積比になる）。
        title: グラフタイトル。
        hole: ドーナツ化する場合の穴の比率（0.0〜1.0、既定0.0=通常の円グラフ）。

    Returns:
        円グラフの `go.Figure`。
    """
    fig = go.Figure(data=[go.Pie(labels=df[names], values=df[values], hole=hole)])
    fig.update_layout(title=title)
    return fig
