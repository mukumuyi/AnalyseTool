"""積み上げ面グラフ（階段状対応）を組み立てる共通モジュール（第1層＝見た目の型）。

時系列に沿った数量の内訳（例: 仕掛数量の3分類の推移）を、階段状の
積み上げ面で表す。`twograph.py`（第2層）がガントチャートと組み合わせて
使う想定のため、既存の `go.Figure` の指定した `row`/`col` にトレースを
追加する `add_area_traces()` を主な入口とし、単体利用向けに
`stacked_area()` という薄いラッパーも用意する。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def add_area_traces(
    fig: go.Figure,
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    color_order: list[str] | None = None,
    colors: dict[str, str] | None = None,
    step: bool = True,
    row: int | None = None,
    col: int | None = None,
) -> go.Figure:
    """既存の `fig` に、`color` 列で内訳分けした積み上げ面のトレースを追加する。

    Args:
        fig: トレースを追加する先の `go.Figure`（単独の図でもsubplotでもよい）。
        df: `x` × `color` の組み合わせごとに1行、`y` に数量を持つデータ。
        x: 横軸の列名（時刻等）。
        y: 積み上げる値の列名。
        color: 内訳の分類列名。
        color_order: 積み上げ順（下から）。省略時はデータの出現順。
        colors: 分類値ごとの色（`{分類値: 色コード}`）。省略時はPlotly既定。
        step: `True`（既定）で階段状（`line_shape="hv"`）にする。
        row, col: subplot内の位置。単独の図に追加する場合は省略する。

    Returns:
        トレース追加後の `fig`（同一オブジェクトを返す）。
    """
    color_order = (
        color_order if color_order is not None else list(dict.fromkeys(df[color]))
    )
    x_order = list(dict.fromkeys(df[x]))

    add_kwargs = {} if row is None else {"row": row, "col": col}
    for color_value in color_order:
        sub = df[df[color] == color_value].set_index(x).reindex(x_order).reset_index()
        line_color = (colors or {}).get(color_value)
        fig.add_trace(
            go.Scatter(
                x=sub[x],
                y=sub[y].fillna(0),
                name=str(color_value),
                mode="lines",
                stackgroup="1",
                line={"shape": "hv" if step else "linear", "color": line_color},
            ),
            **add_kwargs,
        )
    return fig


def stacked_area(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    color_order: list[str] | None = None,
    colors: dict[str, str] | None = None,
    step: bool = True,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """単体の積み上げ面グラフを作る（`add_area_traces()` の薄いラッパー）。"""
    fig = go.Figure()
    add_area_traces(
        fig,
        df,
        x=x,
        y=y,
        color=color,
        color_order=color_order,
        colors=colors,
        step=step,
    )
    fig.update_layout(
        title=title,
        xaxis_title=x_title or x,
        yaxis_title=y_title or y,
        legend_title=color,
    )
    return fig
