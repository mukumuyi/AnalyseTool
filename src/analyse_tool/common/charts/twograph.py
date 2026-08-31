"""x軸共有の2段組グラフを組み立てる共通モジュール（第2層＝分析の型）。

「同じ時間軸を共有する2つのグラフを上下に並べ、ズーム・パンを連動させる」
という分析パターンを、ドメイン知識なしに提供する。実際の描画（上段の
区間の水平棒、下段の積み上げ面）は第1層の`gantt.py`/`area.py`に委譲する。

上段（ガント）は`gantt.py`が1本の`go.Bar`にまとめて追加するため、
`add_gantt_traces()`を先に呼んでおけば、そのトレースは常に
`fig.data[0]`（`curveNumber === 0`）になる。呼び出し側（`visualize.py`側の
クリック処理JS）はこれを使って「クリックされたのが上段（ガント）か
下段（仕掛数量推移）か」を安価に判定できる。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analyse_tool.common.charts.area import add_area_traces
from analyse_tool.common.charts.gantt import add_gantt_traces

GANTT_CURVE_NUMBER = 0
"""ガント側のトレースが必ず占める `curveNumber`。トレース追加順で保証する。"""


def gantt_and_wip_chart(
    gantt_df: pd.DataFrame,
    wip_df: pd.DataFrame,
    *,
    gantt_start: str,
    gantt_end: str,
    gantt_lane: str,
    gantt_label: str,
    gantt_color: str | None = None,
    gantt_colors: dict[str, str] | None = None,
    gantt_min_label_duration: pd.Timedelta | None = None,
    wip_x: str,
    wip_y: str,
    wip_color: str,
    wip_color_order: list[str] | None = None,
    wip_colors: dict[str, str] | None = None,
    title: str | None = None,
    gantt_y_title: str | None = None,
    wip_y_title: str | None = None,
) -> go.Figure:
    """上段=ガント、下段=仕掛数量推移（積み上げ面）の2段組`go.Figure`を作る。

    Args:
        gantt_df, wip_df: それぞれ`gantt.add_gantt_traces()` /
            `area.add_area_traces()`にそのまま渡すデータ。
        gantt_*: `gantt.add_gantt_traces()`に渡す引数（`row`/`col`を除く）。
        wip_*: `area.add_area_traces()`に渡す引数（`row`/`col`を除く）。
        title: グラフ全体のタイトル。
        gantt_y_title, wip_y_title: 上段・下段それぞれの縦軸タイトル。

    Returns:
        `shared_xaxes=True`の2段組`go.Figure`。上段のガントトレースが
        必ず`fig.data[0]`（`GANTT_CURVE_NUMBER`）になる順でトレースを
        追加してある。
    """
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.6, 0.4])

    add_gantt_traces(
        fig,
        gantt_df,
        start=gantt_start,
        end=gantt_end,
        lane=gantt_lane,
        label=gantt_label,
        color=gantt_color,
        colors=gantt_colors,
        min_label_duration=gantt_min_label_duration,
        row=1,
        col=1,
    )
    add_area_traces(
        fig,
        wip_df,
        x=wip_x,
        y=wip_y,
        color=wip_color,
        color_order=wip_color_order,
        colors=wip_colors,
        row=2,
        col=1,
    )

    fig.update_layout(title=title, barmode="stack")
    fig.update_yaxes(title_text=gantt_y_title, type="category", row=1, col=1)
    fig.update_yaxes(title_text=wip_y_title, row=2, col=1)
    return fig
