import pandas as pd

from analyse_tool.common.charts.bar import stacked_bar


def test_stacked_bar_with_color_creates_one_trace_per_color_value():
    df = pd.DataFrame(
        {
            "eqp_id": ["E1", "E2", "E1", "E2"],
            "status": ["busy", "busy", "wait", "wait"],
            "n": [3, 5, 1, 2],
        }
    )

    fig = stacked_bar(df, x="eqp_id", y="n", color="status")

    assert len(fig.data) == 2
    assert {trace.name for trace in fig.data} == {"busy", "wait"}
    assert fig.layout.barmode == "stack"


def test_stacked_bar_without_color_creates_single_unnamed_trace():
    df = pd.DataFrame({"eqp_id": ["E1", "E2"], "n": [8, 7]})

    fig = stacked_bar(df, x="eqp_id", y="n")

    assert len(fig.data) == 1
    assert list(fig.data[0].y) == [8, 7]
    assert fig.layout.showlegend is False


def test_stacked_bar_reindexes_missing_categories_to_zero():
    df = pd.DataFrame({"eqp_id": ["E1"], "n": [8]})

    fig = stacked_bar(df, x="eqp_id", y="n", x_order=["E1", "E2"])

    assert list(fig.data[0].x) == ["E1", "E2"]
    assert (
        list(fig.data[0].y)[1] != list(fig.data[0].y)[1]
    )  # NaN for the missing category
