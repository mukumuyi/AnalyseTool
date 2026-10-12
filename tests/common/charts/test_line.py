import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analyse_tool.common.charts.line import add_line_traces, line


def _df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "t": [1, 2, 3, 1, 2, 3],
            "v": [1.0, 2.0, 3.0, 4.0, np.nan, 6.0],
            "k": ["a", "a", "a", "b", "b", "b"],
        }
    )


def test_one_trace_per_series_with_lines_and_markers():
    fig = line(_df(), x="t", y="v", color="k")
    assert [t.name for t in fig.data] == ["a", "b"]
    assert all(t.mode == "lines+markers" for t in fig.data)
    assert all(isinstance(t, go.Scatter) for t in fig.data)


def test_step_default_false_and_true():
    assert line(_df(), "t", "v", "k").data[0].line.shape == "linear"
    assert line(_df(), "t", "v", "k", step=True).data[0].line.shape == "hv"


def test_missing_values_not_filled():
    trace = line(_df(), "t", "v", "k").data[1]
    assert np.isnan(trace.y[1])
    assert trace.connectgaps is False


def test_color_order_and_colors():
    fig = line(_df(), "t", "v", "k", color_order=["b", "a"], colors={"a": "#ff0000"})
    assert [t.name for t in fig.data] == ["b", "a"]
    assert fig.data[1].line.color == "#ff0000"


def test_row_col_adds_to_subplot():
    fig = make_subplots(rows=2, cols=1)
    returned = add_line_traces(fig, _df(), "t", "v", "k", row=2, col=1)
    assert returned is fig
    assert all(t.yaxis == "y2" for t in fig.data)
