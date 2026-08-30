"""パレート図（件数降順の棒グラフ＋累積構成比の折れ線）を組み立てる共通モジュール。

「上位の項目が全体のどれだけを占めるか」を確認する用途（ABC分析等）を
主に想定。棒は左軸（件数・金額等）、折れ線は右軸（累積構成比0〜100%）に
対応させた二軸グラフとして描く。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def pareto(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """`y` の値が大きい順に並べ替えた棒グラフ＋累積構成比の折れ線を作る。

    Args:
        df: 集計済みデータ（`x`ごとに1行、`y`に件数・金額等）。`y`降順に
            並んでいる必要はない（本関数内で並べ替える）。
        x: 横軸のカテゴリ列名。
        y: 棒の高さに使う値の列名（この値の降順で並べ替える）。
        title, x_title, y_title: グラフ・軸のタイトル（`y_title`は棒側の左軸）。

    Returns:
        棒（左軸）＋累積構成比の折れ線（右軸、0〜100%）を重ねた `go.Figure`。
    """
    sorted_df = df.sort_values(y, ascending=False).reset_index(drop=True)
    cumulative_pct = sorted_df[y].cumsum() / sorted_df[y].sum() * 100

    fig = go.Figure()
    fig.add_trace(go.Bar(x=sorted_df[x], y=sorted_df[y], name=y_title or y))
    fig.add_trace(
        go.Scatter(
            x=sorted_df[x],
            y=cumulative_pct,
            name="累積構成比",
            mode="lines+markers",
            yaxis="y2",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title=x_title or x,
        yaxis_title=y_title or y,
        xaxis={
            "categoryorder": "array",
            "categoryarray": sorted_df[x].tolist(),
        },
        yaxis2={
            "title": "累積構成比(%)",
            "overlaying": "y",
            "side": "right",
            "range": [0, 100],
        },
    )
    return fig
