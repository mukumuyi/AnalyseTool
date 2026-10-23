"""棒＋第2軸の折れ線グラフを組み立てる共通モジュール（第1層＝見た目の型）。

「カテゴリごとの棒」と「同じ横軸に対する第2軸の折れ線」を重ねる見た目を、
ドメイン知識なしに提供する。棒は `color` を指定すると積み上げ、省略すると
単色になる。パレート図（棒＋累積構成比の折れ線）・時間帯別の稼働状況
（積み上げ棒＋着工件数の折れ線）など、複数の分析パターンの土台になる
（実際の使い分けは `common/charts/pareto.py` 等の第2層が担う）。

第1層どうしは依存しない方針のため、`bar.py` は使わず棒の描画もここで
完結させる。
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go


def bar_with_line(
    df: pd.DataFrame,
    x: str,
    y_bar: str,
    y_line: str,
    color: str | None = None,
    x_order: list[Any] | None = None,
    title: str | None = None,
    x_title: str | None = None,
    y_bar_title: str | None = None,
    y_line_title: str | None = None,
    line_name: str | None = None,
) -> go.Figure:
    """棒（主軸）＋折れ線（第2軸）を重ねた `go.Figure` を作る。

    Args:
        df: 集計済みデータ。`color` 指定時は `x` × `color` ごとに1行。
        x: 横軸の列名（カテゴリ）。
        y_bar: 棒（主軸）の値の列名。
        y_line: 折れ線（第2軸）の値の列名。`x` ごとに1つの値である前提
            （`color` 指定時、同じ `x` の複数行に同じ値が入っていてよい。
            内部で `x` ごとに重複排除してから折れ線を引く）。
        color: 棒を色分け（積み上げ）する列名。省略時は単色棒。
        x_order: 横軸カテゴリの表示順。省略時はデータの出現順。
        title, x_title, y_bar_title, y_line_title: グラフ・軸のタイトル。
        line_name: 凡例上の折れ線の名前。

    Returns:
        棒（`yaxis`）と折れ線（`yaxis2`、右側）を重ねた `go.Figure`。
        棒のトレースは `color` 値ごと（またはトレース名 `y_bar`）、
        折れ線のトレースは末尾に1本追加される。
    """
    x_order = x_order if x_order is not None else list(dict.fromkeys(df[x]))

    fig = go.Figure()
    if color is None:
        sub = df.set_index(x).reindex(x_order).reset_index()
        fig.add_trace(go.Bar(x=sub[x], y=sub[y_bar], name=y_bar_title or y_bar))
    else:
        for color_value, sub in df.groupby(color, sort=False):
            sub = sub.set_index(x).reindex(x_order).reset_index()
            fig.add_trace(
                go.Bar(
                    x=sub[x],
                    y=sub[y_bar],
                    name=str(color_value),
                )
            )

    line_df = df.drop_duplicates(subset=[x]).set_index(x).reindex(x_order).reset_index()
    fig.add_trace(
        go.Scatter(
            x=line_df[x],
            y=line_df[y_line],
            name=line_name or y_line_title or y_line,
            mode="lines+markers",
            yaxis="y2",
        )
    )

    fig.update_layout(
        barmode="stack",
        title=title,
        xaxis_title=x_title or x,
        yaxis_title=y_bar_title or y_bar,
        xaxis={"categoryorder": "array", "categoryarray": x_order},
        yaxis2={
            "title": y_line_title or y_line,
            "overlaying": "y",
            "side": "right",
        },
        legend={"orientation": "h", "y": -0.2},
        legend_title=color,
    )
    return fig
