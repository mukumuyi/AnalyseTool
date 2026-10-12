"""円グラフ（構成比）を組み立てる共通モジュール。

`analyze.py` で集計済みの小さいデータ（カテゴリ×値）を受け取り、
Plotlyの `Figure` を返すだけの関数を持つ。ツールをまたいで使い回す想定なので、
特定ツールの列名・ドメイン知識には依存しない。
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go


def pie(
    df: pd.DataFrame,
    names: str,
    values: str,
    names_order: list[Any] | None = None,
    colors: dict[Any, str] | None = None,
    title: str | None = None,
    hole: float = 0.0,
) -> go.Figure:
    """円グラフ（`hole` 指定でドーナツ）を作る。

    カテゴリが多い場合（目安10超）はスライスが読めなくなるため対象外。
    棒グラフ／パレート図を使うか、呼び出し側で「上位N件＋その他」に集計すること。

    Args:
        df: 集計済みデータ。`names` 列（カテゴリ）と `values` 列（値）を持つ。
            値が欠損・0以下の行は除外し、同一カテゴリの重複行は合算する。
        names: カテゴリの列名。
        values: 値の列名。
        names_order: カテゴリの表示順。省略時はデータの出現順。
            含まれないカテゴリは描画しない。
        colors: カテゴリ→色の対応。未指定のカテゴリは Plotly の既定色。
        title: グラフのタイトル。
        hole: 中央の穴の大きさ（0〜1）。0で円、0より大きいとドーナツ。

    Returns:
        `go.Pie` を1トレース持つ `go.Figure`。
    """
    order = names_order if names_order is not None else list(dict.fromkeys(df[names]))

    nums = pd.to_numeric(df[values], errors="coerce")
    valid = df.assign(**{values: nums})
    valid = valid[valid[values] > 0]
    totals = valid.groupby(names, sort=False)[values].sum()
    labels = [name for name in order if name in totals.index]

    marker = None
    if colors is not None:
        marker = {"colors": [colors.get(name) for name in labels]}

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=[totals[name] for name in labels],
            sort=False,
            hole=hole,
            marker=marker,
            textinfo="label+percent",
            hovertemplate="%{label}<br>%{value}（%{percent}）<extra></extra>",
        )
    )
    fig.update_layout(title=title, showlegend=True)
    return fig
