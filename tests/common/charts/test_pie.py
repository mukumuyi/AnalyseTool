import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analyse_tool.common.charts.pie import pie


def _df() -> pd.DataFrame:
    return pd.DataFrame({"k": ["a", "b", "c"], "v": [1, 2, 3]})


def test_single_pie_trace():
    fig = pie(_df(), "k", "v")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert isinstance(fig.data[0], go.Pie)


def test_default_order_is_appearance_and_sort_false():
    trace = pie(_df(), "k", "v").data[0]
    assert list(trace.labels) == ["a", "b", "c"]
    assert trace.sort is False


def test_names_order_applied_and_unknown_ignored():
    trace = pie(_df(), "k", "v", names_order=["c", "x", "a"]).data[0]
    assert list(trace.labels) == ["c", "a"]
    assert list(trace.values) == [3, 1]


def test_zero_negative_and_missing_excluded():
    df = pd.DataFrame({"k": ["a", "b", "c", "d"], "v": [1, 0, -2, np.nan]})
    trace = pie(df, "k", "v").data[0]
    assert list(trace.labels) == ["a"]
    assert list(trace.values) == [1]


def test_duplicate_categories_summed():
    df = pd.DataFrame({"k": ["a", "b", "a"], "v": [1, 2, 4]})
    trace = pie(df, "k", "v").data[0]
    assert list(trace.labels) == ["a", "b"]
    assert list(trace.values) == [5, 2]


def test_categorical_excludes_zero_and_unknown_categories():
    df = pd.DataFrame(
        {
            "k": pd.Categorical(["a", "b", "c"], categories=["a", "b", "c", "d"]),
            "v": [1, 0, 3],
        }
    )
    trace = pie(df, "k", "v", names_order=["a", "b", "c", "d"]).data[0]
    assert list(trace.labels) == ["a", "c"]
    assert list(trace.values) == [1, 3]


def test_duplicate_names_order_deduplicated():
    trace = pie(_df(), "k", "v", names_order=["a", "b", "a"]).data[0]
    assert list(trace.labels) == ["a", "b"]
    assert list(trace.values) == [1, 2]


def test_numeric_strings_treated_as_numbers():
    df = pd.DataFrame({"k": ["a", "b", "c"], "v": ["1", "2", "x"]})
    trace = pie(df, "k", "v").data[0]
    assert list(trace.labels) == ["a", "b"]
    assert list(trace.values) == [1, 2]


def test_empty_dataframe_returns_empty_pie():
    df = pd.DataFrame({"k": [], "v": []})
    fig = pie(df, "k", "v")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    trace = fig.data[0]
    assert isinstance(trace, go.Pie)
    assert len(trace.labels) == 0
    assert len(trace.values) == 0


def test_all_rows_excluded_returns_empty_pie():
    df = pd.DataFrame({"k": ["a", "b"], "v": [0, -1]})
    trace = pie(df, "k", "v").data[0]
    assert len(trace.labels) == 0
    assert len(trace.values) == 0


def test_colors_follow_label_order():
    trace = pie(_df(), "k", "v", colors={"a": "#111111", "c": "#333333"}).data[0]
    assert list(trace.marker.colors) == ["#111111", None, "#333333"]


def test_no_colors_by_default():
    assert pie(_df(), "k", "v").data[0].marker.colors is None


def test_hole_default_and_specified():
    assert pie(_df(), "k", "v").data[0].hole == 0
    assert pie(_df(), "k", "v", hole=0.4).data[0].hole == 0.4
