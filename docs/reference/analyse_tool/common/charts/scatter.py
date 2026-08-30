"""散布図を組み立てる共通モジュール。

2つの数値列の関係（相関・分布の広がり）を確認する用途を主に想定。
CLAUDE.mdの方針に従い、大量点でも滑らかに描画できるようWebGLレンダラ
（`go.Scattergl`）を既定にする（`go.Scatter`は使わない）。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    size: str | None = None,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """数値列 `x`×`y` の関係を散布図（WebGL）で表す。

    Args:
        df: 元データ。大量データの場合は`analyze.py`側で表示に必要な粒度まで
            サンプリング・間引きしてから渡す（本関数側では間引かない）。
        x, y: 横軸・縦軸の数値列名。
        color: 色分けするカテゴリ列名（省略時は単色）。
        size: 点の大きさに使う数値列名（省略時は固定サイズ）。
        title, x_title, y_title: グラフ・軸のタイトル。

    Returns:
        散布図の `go.Figure`（`go.Scattergl`ベース）。`color`指定時は
        カテゴリごとに1トレース。
    """
    fig = go.Figure()
    if color is None:
        fig.add_trace(
            go.Scattergl(x=df[x], y=df[y], mode="markers", marker=_marker(df, size))
        )
    else:
        for category, sub in df.groupby(color, sort=False):
            fig.add_trace(
                go.Scattergl(
                    x=sub[x],
                    y=sub[y],
                    mode="markers",
                    marker=_marker(sub, size),
                    name=str(category),
                )
            )

    fig.update_layout(
        title=title,
        xaxis_title=x_title or x,
        yaxis_title=y_title or y,
        legend_title=color,
    )
    return fig


def _marker(df: pd.DataFrame, size: str | None) -> dict:
    return {"size": df[size]} if size else {}
