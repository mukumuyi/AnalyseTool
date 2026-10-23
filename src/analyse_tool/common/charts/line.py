"""折れ線グラフ（線＋点）を組み立てる共通モジュール（第1層＝見た目の型）。

時系列等に沿った値の推移を、`color` 列の分類ごとの折れ線で表す。
`area.py` と同様、既存の `go.Figure` の指定した `row`/`col` にトレースを
追加する `add_line_traces()` を主な入口とし、単体利用向けに `line()` という
薄いラッパーも用意する。描画は `bar.py` と同様に SVG の `go.Scatter` を使う。

欠損は補完せず、`NaN` のまま線を途切れさせる（0 と誤読させないため）。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def add_line_traces(
    fig: go.Figure,
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    color_order: list[str] | None = None,
    colors: dict[str, str] | None = None,
    step: bool = False,
    row: int | None = None,
    col: int | None = None,
) -> go.Figure:
    """既存の `fig` に、`color` 列で系列分けした折れ線（線＋点）のトレースを追加する。

    Args:
        fig: トレースを追加する先の `go.Figure`（単独の図でもsubplotでもよい）。
        df: `x` × `color` の組み合わせごとに1行、`y` に値を持つデータ。
        x: 横軸の列名（時刻等）。
        y: 縦軸の値の列名。欠損（`NaN`）は補完せず線を途切れさせる。
        color: 系列の分類列名。単一系列の場合は定数列を渡す。
        color_order: 系列の描画順（凡例順）。省略時はデータの出現順。
        colors: 系列ごとの色（`{分類値: 色コード}`）。省略時はPlotly既定。
        step: `True` で階段状（`line_shape="hv"`）にする。既定は直線補間。
        row, col: subplot内の位置。単独の図に追加する場合は省略する。

    Returns:
        トレース追加後の `fig`（同一オブジェクトを返す）。
    """
    color_order = (
        color_order if color_order is not None else list(dict.fromkeys(df[color]))
    )

    add_kwargs = {} if row is None else {"row": row, "col": col}
    for color_value in color_order:
        sub = df[df[color] == color_value].sort_values(x)
        line_color = (colors or {}).get(color_value)
        fig.add_trace(
            go.Scatter(
                x=sub[x],
                y=sub[y],
                name=str(color_value),
                mode="lines+markers",
                connectgaps=False,
                line={"shape": "hv" if step else "linear", "color": line_color},
            ),
            **add_kwargs,
        )
    return fig


def line(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    color_order: list[str] | None = None,
    colors: dict[str, str] | None = None,
    step: bool = False,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """単体の折れ線グラフを作る（`add_line_traces()` の薄いラッパー）。"""
    fig = go.Figure()
    add_line_traces(
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
