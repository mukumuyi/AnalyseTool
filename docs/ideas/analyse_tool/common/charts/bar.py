"""棒グラフ（積み上げ棒グラフ）を組み立てる共通モジュール。

`analyze.py` で集計済みの小さいデータ（カテゴリ×色分け軸×件数）を受け取り、
Plotlyの `Figure` を返すだけの関数を持つ。ツールをまたいで使い回す想定なので、
特定ツールの列名・ドメイン知識には依存しない。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def stacked_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    x_order: list[str] | None = None,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """カテゴリごとに `color` 列で色分けした積み上げ棒グラフを作る。

    Args:
        df: 集計済みデータ（`x` × `color` の組み合わせごとに1行、`y` に件数等）。
        x: 横軸の列名（カテゴリ）。
        y: 縦軸の列名（値・件数）。
        color: 色分けする列名（積み上げの内訳）。
        x_order: 横軸カテゴリの表示順。省略時はデータの出現順。
        title, x_title, y_title: グラフ・軸のタイトル。

    Returns:
        積み上げ棒グラフの `go.Figure`。各色分け値ごとに1トレース。
        クリックイベントで `data.name`（= `color` の値）と `x`（= 横軸カテゴリ）を
        拾えるよう、トレース名を `color` の値そのものにしている。
    """
    x_order = x_order if x_order is not None else list(dict.fromkeys(df[x]))

    fig = go.Figure()
    for color_value, sub in df.groupby(color, sort=False):
        sub = sub.set_index(x).reindex(x_order).reset_index()
        fig.add_trace(
            go.Bar(
                x=sub[x],
                y=sub[y],
                name=str(color_value),
            )
        )

    fig.update_layout(
        barmode="stack",
        title=title,
        xaxis_title=x_title or x,
        yaxis_title=y_title or y,
        xaxis={"categoryorder": "array", "categoryarray": x_order},
        legend_title=color,
    )
    return fig
