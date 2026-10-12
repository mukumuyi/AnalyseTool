"""散布図を組み立てる共通モジュール（第1層＝見た目の型）。

数百〜数千点程度でも描画が重くならないよう、常に `scattergl`
（WebGL描画）を使う。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    text: str | None = None,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """`x`×`y` の散布図（`scattergl`固定）を作る。

    Args:
        df: 点ごとのデータ（1点1行）。
        x, y: 横軸・縦軸の値の列名。
        text: ホバー時に表示するラベル（例: eqp_id）の列名。省略可。
        title, x_title, y_title: グラフ・軸のタイトル。

    Returns:
        散布図の `go.Figure`（1トレース、`mode="markers"`）。
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scattergl(
            x=df[x],
            y=df[y],
            mode="markers",
            text=df[text] if text is not None else None,
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title=x_title or x,
        yaxis_title=y_title or y,
    )
    return fig
