import pandas as pd

from analyse_tool.common.charts.box import box


def test_box_without_x_makes_a_single_trace():
    df = pd.DataFrame({"amount": [10, 20, 30]})

    fig = box(df, y="amount")

    assert len(fig.data) == 1
    assert list(fig.data[0].y) == [10, 20, 30]


def test_box_with_x_makes_one_trace_per_category():
    df = pd.DataFrame(
        {
            "seg": ["法人", "法人", "個人"],
            "amount": [10, 20, 30],
        }
    )

    fig = box(df, y="amount", x="seg")

    assert [trace.name for trace in fig.data] == ["法人", "個人"]
    assert list(fig.data[0].y) == [10, 20]
    assert list(fig.data[1].y) == [30]
    assert fig.layout.showlegend is True


def test_box_titles_default_to_column_names():
    df = pd.DataFrame({"amount": [1, 2]})

    fig = box(df, y="amount")

    assert fig.layout.yaxis.title.text == "amount"
