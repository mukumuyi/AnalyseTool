import math

import pandas as pd

from analyse_tool.common.charts.pareto import pareto


def test_pareto_sorts_bars_by_value_descending():
    df = pd.DataFrame({"cat": ["c", "a", "b"], "count": [30, 50, 20]})

    fig = pareto(df, x="cat", y="count")
    bar_trace, _line_trace = fig.data

    assert list(bar_trace.x) == ["a", "c", "b"]
    assert list(bar_trace.y) == [50, 30, 20]
    assert fig.layout.xaxis.categoryarray == ("a", "c", "b")


def test_pareto_cumulative_percentage_reaches_100():
    df = pd.DataFrame({"cat": ["c", "a", "b"], "count": [30, 50, 20]})

    fig = pareto(df, x="cat", y="count")
    _bar_trace, line_trace = fig.data

    assert math.isclose(line_trace.y[0], 50.0)
    assert math.isclose(line_trace.y[1], 80.0)
    assert math.isclose(line_trace.y[2], 100.0)


def test_pareto_line_is_on_the_secondary_right_axis():
    df = pd.DataFrame({"cat": ["a", "b"], "count": [1, 1]})

    fig = pareto(df, x="cat", y="count")
    _bar_trace, line_trace = fig.data

    assert line_trace.yaxis == "y2"
    assert fig.layout.yaxis2.side == "right"
    assert fig.layout.yaxis2.range == (0, 100)
