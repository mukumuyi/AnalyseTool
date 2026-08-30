"""箱ひげ図（boxplot）を組み立てる共通モジュール。

EDA（前準備）で数値列の分布・ばらつき・外れ値を確認する用途を主に想定。
`x`でカテゴリ列を指定すると、カテゴリごとに箱ひげ図を並べて比較できる。
特定ツールの列名・ドメイン知識には依存しない。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def box(
    df: pd.DataFrame,
    y: str,
    x: str | None = None,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """数値列 `y` の分布を箱ひげ図で表す。

    Args:
        df: 元データ。行数が多い場合は事前に`analyze.py`側で必要な列だけに
            絞り込んでおく（本関数側では間引かない）。
        y: 分布を見たい数値列名。
        x: カテゴリ列名（省略時は全体で1本の箱ひげ図）。
        title, x_title, y_title: グラフ・軸のタイトル。

    Returns:
        箱ひげ図の `go.Figure`。`x`指定時はカテゴリごとに1トレース。
    """
    fig = go.Figure()
    if x is None:
        fig.add_trace(go.Box(y=df[y], name=y_title or y))
    else:
        for category, sub in df.groupby(x, sort=False):
            fig.add_trace(go.Box(y=sub[y], name=str(category)))

    fig.update_layout(
        title=title,
        xaxis_title=x_title or x,
        yaxis_title=y_title or y,
        showlegend=x is not None,
    )
    return fig
