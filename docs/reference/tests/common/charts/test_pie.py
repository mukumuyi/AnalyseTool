import pandas as pd

from analyse_tool.common.charts.pie import pie


def test_pie_builds_a_single_pie_trace():
    df = pd.DataFrame({"seg": ["法人", "個人", "官公庁"], "count": [10, 20, 5]})

    fig = pie(df, names="seg", values="count", title="内訳")

    assert len(fig.data) == 1
    assert fig.data[0].type == "pie"
    assert list(fig.data[0].labels) == ["法人", "個人", "官公庁"]
    assert list(fig.data[0].values) == [10, 20, 5]
    assert fig.layout.title.text == "内訳"


def test_pie_hole_defaults_to_0_and_can_be_set_for_a_donut():
    df = pd.DataFrame({"seg": ["A", "B"], "count": [1, 1]})

    assert pie(df, names="seg", values="count").data[0].hole == 0.0
    assert pie(df, names="seg", values="count", hole=0.4).data[0].hole == 0.4
