"""ヒストグラムを組み立てる共通モジュール。

EDA（前準備）で数値列の分布形状（山の数・裾の広がり・偏り）を確認する
用途を主に想定。`color`でカテゴリ別に半透明で重ねて比較することもできる。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def histogram(
    df: pd.DataFrame,
    x: str,
    color: str | None = None,
    nbins: int | None = None,
    histnorm: str | None = None,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """数値列 `x` の分布をヒストグラムで表す。

    Args:
        df: 元データ。
        x: 分布を見たい数値列名。
        color: カテゴリ列名（省略時は全体で1本。指定時はカテゴリごとに
            半透明で重ねて表示する）。
        nbins: ビン数（省略時はPlotly側の自動決定）。
        histnorm: Plotlyの`histnorm`（例: `"percent"`で各ビンの構成比表示。
            省略時は件数そのまま）。
        title, x_title, y_title: グラフ・軸のタイトル。

    Returns:
        ヒストグラムの `go.Figure`。`color`指定時はカテゴリごとに1トレース
        （`barmode="overlay"`で重ね描き）。
    """
    fig = go.Figure()
    if color is None:
        fig.add_trace(go.Histogram(x=df[x], nbinsx=nbins, histnorm=histnorm))
    else:
        for category, sub in df.groupby(color, sort=False):
            fig.add_trace(
                go.Histogram(x=sub[x], nbinsx=nbins, histnorm=histnorm, name=str(category))
            )
        fig.update_layout(barmode="overlay")
        fig.update_traces(opacity=0.6)

    fig.update_layout(
        title=title,
        xaxis_title=x_title or x,
        yaxis_title=y_title or (histnorm or "件数"),
        legend_title=color,
    )
    return fig
