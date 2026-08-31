"""棒グラフ（単色棒／積み上げ棒グラフ）を組み立てる共通モジュール。

`analyze.py` で集計済みの小さいデータ（カテゴリ×件数、または
カテゴリ×色分け軸×件数）を受け取り、Plotlyの `Figure` を返すだけの
関数を持つ。ツールをまたいで使い回す想定なので、特定ツールの
列名・ドメイン知識には依存しない。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def stacked_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    x_order: list[str] | None = None,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """棒グラフを作る。`color` を指定すると積み上げ棒、省略すると単色棒になる。

    Args:
        df: 集計済みデータ。`color` 指定時は `x` × `color` の組み合わせごとに
            1行、`y` に件数等。`color` 省略時は `x` ごとに1行。
        x: 横軸の列名（カテゴリ）。
        y: 縦軸の列名（値・件数）。
        color: 色分けする列名（積み上げの内訳）。省略時は単色棒になる。
        x_order: 横軸カテゴリの表示順。省略時はデータの出現順。
        title, x_title, y_title: グラフ・軸のタイトル。

    Returns:
        棒グラフの `go.Figure`。`color` 指定時は色分け値ごとに1トレース
        （クリックイベントで `data.name` = `color` の値、`x` = 横軸カテゴリを
        拾える）。`color` 省略時は単色の1トレースのみ。
    """
    x_order = x_order if x_order is not None else list(dict.fromkeys(df[x]))

    fig = go.Figure()
    if color is None:
        sub = df.set_index(x).reindex(x_order).reset_index()
        fig.add_trace(go.Bar(x=sub[x], y=sub[y]))
    else:
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
        showlegend=color is not None,
        legend_title=color,
    )
    return fig
