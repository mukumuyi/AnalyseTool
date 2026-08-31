import pandas as pd

from analyse_tool.common.charts.gantt import add_gantt_traces, gantt_chart


def _segments_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "lane": [0, 0, 1],
            "start": pd.to_datetime(
                ["2026-01-01 00:00", "2026-01-01 01:00", "2026-01-01 00:30"]
            ),
            "end": pd.to_datetime(
                ["2026-01-01 00:50", "2026-01-01 02:00", "2026-01-01 00:35"]
            ),
            "lot_id": ["LOT001", "LOT002", "LOT003"],
            "status": ["busy", "busy", "wait"],
        }
    )


def test_gantt_chart_is_a_single_vectorized_bar_trace():
    fig = gantt_chart(
        _segments_df(),
        start="start",
        end="end",
        lane="lane",
        label="lot_id",
        color="status",
    )

    assert len(fig.data) == 1
    trace = fig.data[0]
    assert trace.type == "bar"
    assert trace.orientation == "h"
    assert list(trace.y) == [0, 0, 1]


def test_gantt_chart_applies_color_map():
    fig = gantt_chart(
        _segments_df(),
        start="start",
        end="end",
        lane="lane",
        label="lot_id",
        color="status",
        colors={"busy": "steelblue", "wait": "lightgray"},
    )

    assert list(fig.data[0].marker.color) == ["steelblue", "steelblue", "lightgray"]


def test_min_label_duration_hides_labels_on_short_segments():
    fig = gantt_chart(
        _segments_df(),
        start="start",
        end="end",
        lane="lane",
        label="lot_id",
        min_label_duration=pd.Timedelta(minutes=15),
    )

    # LOT003 is only 5 minutes long -> label suppressed
    assert list(fig.data[0].text) == ["LOT001", "LOT002", ""]


def test_add_gantt_traces_is_the_first_trace_when_added_before_other_traces():
    import plotly.graph_objects as go

    fig = go.Figure()
    add_gantt_traces(
        fig, _segments_df(), start="start", end="end", lane="lane", label="lot_id"
    )
    fig.add_trace(go.Scatter(x=[1, 2], y=[1, 2]))

    assert fig.data[0].type == "bar"


def test_gantt_chart_forces_the_x_axis_to_date_type():
    # 回帰テスト: `x`（所要時間）が数値のため、軸型の自動判定に任せると
    # 日時軸と認識されず、`base`（開始時刻）が位置として解釈されずに
    # 全区間がx=0起点で描かれてしまう不具合があった。
    fig = gantt_chart(
        _segments_df(), start="start", end="end", lane="lane", label="lot_id"
    )

    assert fig.layout.xaxis.type == "date"


def test_add_gantt_traces_forces_date_type_on_the_target_subplot_axis():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=2, cols=1)
    add_gantt_traces(
        fig,
        _segments_df(),
        start="start",
        end="end",
        lane="lane",
        label="lot_id",
        row=1,
        col=1,
    )
    fig.add_trace(go.Scatter(x=[1, 2], y=[1, 2]), row=2, col=1)

    assert fig.layout.xaxis.type == "date"
    assert fig.layout.xaxis2.type != "date"
