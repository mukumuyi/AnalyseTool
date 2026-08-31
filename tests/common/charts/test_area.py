import pandas as pd
import plotly.graph_objects as go

from analyse_tool.common.charts.area import add_area_traces, stacked_area


def _wip_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "t": [1, 2, 1, 2, 1, 2],
            "cat": [
                "busy",
                "busy",
                "wait_self",
                "wait_self",
                "wait_other",
                "wait_other",
            ],
            "n": [1, 2, 3, 4, 5, 6],
        }
    )


def test_stacked_area_creates_one_trace_per_category_with_stackgroup():
    fig = stacked_area(_wip_df(), x="t", y="n", color="cat")

    assert len(fig.data) == 3
    assert all(trace.stackgroup == "1" for trace in fig.data)
    assert [trace.name for trace in fig.data] == ["busy", "wait_self", "wait_other"]


def test_add_area_traces_respects_explicit_color_order_and_step_shape():
    fig = go.Figure()
    add_area_traces(
        fig,
        _wip_df(),
        x="t",
        y="n",
        color="cat",
        color_order=["wait_other", "wait_self", "busy"],
        step=True,
    )

    assert [trace.name for trace in fig.data] == ["wait_other", "wait_self", "busy"]
    assert all(trace.line.shape == "hv" for trace in fig.data)


def test_add_area_traces_can_target_a_subplot_row_col():
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=2, cols=1)
    add_area_traces(fig, _wip_df(), x="t", y="n", color="cat", row=2, col=1)

    assert len(fig.data) == 3
    for trace in fig.data:
        assert trace.xaxis == "x2"
        assert trace.yaxis == "y2"
