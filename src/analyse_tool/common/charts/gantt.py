"""区間の水平棒（ガントチャート）を組み立てる共通モジュール（第1層＝見た目の型）。

「並行処理枠（行）ごとに、開始〜終了の区間を横棒で表す」という見た目を、
ドメイン知識なしに提供する。区間数が多くなりうる（同時並行数×件数）ため、
`add_trace()` を区間ごとに呼ばず、`base`（開始時刻）・`x`（所要時間）・
`y`（行）・`marker_color`・`text` を配列にまとめた**1本の `go.Bar`**として
描画する。`twograph.py`（第2層）が仕掛数量推移と組み合わせて使う想定
のため、既存の `go.Figure` に追加する `add_gantt_traces()` を主な入口とし、
単体利用向けに `gantt_chart()` という薄いラッパーも用意する。

1本のトレースにまとめることで、`twograph.py` はこのトレースの
`curveNumber` を固定できる（2段構成の中でガント側のクリックだけを
判定するため）。
"""

from __future__ import annotations

import pandas as pd
import plotly.colors
import plotly.graph_objects as go


def _default_color_map(values: pd.Series) -> dict[str, str]:
    """色分け値ごとに、Plotly既定の定性配色を出現順に割り当てる。

    `colors` を省略したとき用のフォールバック。カテゴリ値そのもの
    （例: `"busy"`）は`go.Bar(marker_color=...)`が要求するCSS色表現では
    ないため、そのまま渡すとエラーになる。
    """
    palette = plotly.colors.qualitative.Plotly
    unique_values = list(dict.fromkeys(values))
    return {v: palette[i % len(palette)] for i, v in enumerate(unique_values)}


def add_gantt_traces(
    fig: go.Figure,
    df: pd.DataFrame,
    start: str,
    end: str,
    lane: str,
    label: str,
    color: str | None = None,
    colors: dict[str, str] | None = None,
    min_label_duration: pd.Timedelta | None = None,
    row: int | None = None,
    col: int | None = None,
) -> go.Figure:
    """既存の `fig` に、区間ごとの横棒を1本の `go.Bar` として追加する。

    Args:
        fig: トレースを追加する先の `go.Figure`（単独の図でもsubplotでもよい）。
        df: 区間データ（1区間1行）。
        start, end: 区間の開始・終了時刻の列名。
        lane: 並行処理枠（行）の列名。同じ値の行は同じ横列に描かれる。
        label: 区間内に表示するラベル（例: ロットID）の列名。
        color: 区間の色分けに使う列名（例: ステータス）。省略時は既定色。
        colors: 色分け値ごとの色（`{値: 色コード}`）。
        min_label_duration: この所要時間未満の区間はラベルを表示しない
            （区間が狭くて文字が収まらない場合の出し分け）。省略時は常に表示。
        row, col: subplot内の位置。単独の図に追加する場合は省略する。

    Returns:
        トレース追加後の `fig`（同一オブジェクトを返す）。
    """
    durations = df[end] - df[start]
    if min_label_duration is not None:
        text = [
            str(lbl) if dur >= min_label_duration else ""
            for lbl, dur in zip(df[label], durations, strict=True)
        ]
    else:
        text = [str(v) for v in df[label]]

    marker_color = None
    if color is not None:
        resolved_colors = (
            colors if colors is not None else _default_color_map(df[color])
        )
        marker_color = [resolved_colors[v] for v in df[color]]

    add_kwargs = {} if row is None else {"row": row, "col": col}
    fig.add_trace(
        go.Bar(
            base=list(df[start]),
            x=list(durations),
            y=list(df[lane]),
            orientation="h",
            text=text,
            textposition="inside",
            hovertext=[str(v) for v in df[label]],
            marker_color=marker_color,
        ),
        **add_kwargs,
    )
    # `base`（区間の開始時刻）は日時型だが、`x`（所要時間）はただの数値のため、
    # 軸の型をPlotly側の自動判定に任せると日時軸と認識されず、`base`が
    # 位置として解釈されずに全区間がx=0起点で描かれてしまう。明示的に
    # 日時軸を指定する（ブラウザでの動作確認で判明した不具合の対策）。
    fig.update_xaxes(type="date", **add_kwargs)
    return fig


def gantt_chart(
    df: pd.DataFrame,
    start: str,
    end: str,
    lane: str,
    label: str,
    color: str | None = None,
    colors: dict[str, str] | None = None,
    min_label_duration: pd.Timedelta | None = None,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """単体のガントチャートを作る（`add_gantt_traces()` の薄いラッパー）。"""
    fig = go.Figure()
    add_gantt_traces(
        fig,
        df,
        start=start,
        end=end,
        lane=lane,
        label=label,
        color=color,
        colors=colors,
        min_label_duration=min_label_duration,
    )
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        yaxis={"type": "category"},
        showlegend=False,
    )
    return fig
