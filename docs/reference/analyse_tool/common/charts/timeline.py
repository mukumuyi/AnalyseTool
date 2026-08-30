"""ガントチャート（期間の横棒）を組み立てる共通モジュール。

タスク・イベントごとの開始〜終了期間を横棒で並べ、スケジュールや稼働期間の
重なりを確認する用途を主に想定。特定ツールの列名・ドメイン知識には
依存しない。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def timeline(
    df: pd.DataFrame,
    task: str,
    start: str,
    finish: str,
    color: str | None = None,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """タスク（`task`）ごとの期間（`start`〜`finish`）を横棒で並べたガントチャートを作る。

    Args:
        df: 期間データ（`task`ごとに1行、`start`/`finish`は日付列）。
        task: 縦軸に並べるタスク・カテゴリ列名。表示順は`df`の行順に従う
            （並べ替えが必要な場合は`analyze.py`側で事前にソートしておく）。
        start, finish: 開始日・終了日の列名（日付型、または日付に変換できる値）。
        color: 色分けするカテゴリ列名（省略時は単色。工程種別などに使う）。
        title, x_title, y_title: グラフ・軸のタイトル。

    Returns:
        期間を横棒で表すガントチャートの `go.Figure`（`go.Bar`の
        `orientation="h"`＋`base`に開始日を指定して組み立てる）。
    """
    df = df.copy()
    duration = pd.to_datetime(df[finish]) - pd.to_datetime(df[start])

    fig = go.Figure()
    if color is None:
        fig.add_trace(go.Bar(base=df[start], x=duration, y=df[task], orientation="h"))
    else:
        for category, sub in df.groupby(color, sort=False):
            fig.add_trace(
                go.Bar(
                    base=sub[start],
                    x=duration.loc[sub.index],
                    y=sub[task],
                    orientation="h",
                    name=str(category),
                )
            )

    fig.update_layout(
        title=title,
        xaxis_title=x_title or "期間",
        yaxis_title=y_title or task,
        xaxis={"type": "date"},
        legend_title=color,
        barmode="overlay",
    )
    # 上から時系列順に見せるため、Plotlyの既定（下から並ぶ）を反転する。
    fig.update_yaxes(autorange="reversed")
    return fig
