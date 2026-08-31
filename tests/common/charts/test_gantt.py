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
