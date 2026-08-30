import pandas as pd

from analyse_tool.common.charts.scatter import scatter


def test_scatter_uses_webgl_renderer():
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})

    fig = scatter(df, x="x", y="y")

    assert len(fig.data) == 1
    assert fig.data[0].type == "scattergl"
    assert fig.data[0].marker.size is None


def test_scatter_size_column_is_forwarded_to_marker_size():
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4], "weight": [5, 6]})

    fig = scatter(df, x="x", y="y", size="weight")

    assert list(fig.data[0].marker.size) == [5, 6]


def test_scatter_with_color_makes_one_trace_per_category():
    df = pd.DataFrame(
        {
            "x": [1, 2, 3],
            "y": [4, 5, 6],
            "seg": ["A", "A", "B"],
        }
    )

    fig = scatter(df, x="x", y="y", color="seg")

    assert [trace.name for trace in fig.data] == ["A", "B"]
    assert list(fig.data[0].x) == [1, 2]
    assert list(fig.data[1].x) == [3]
