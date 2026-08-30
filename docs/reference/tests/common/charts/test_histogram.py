import pandas as pd

from analyse_tool.common.charts.histogram import histogram


def test_histogram_without_color_makes_a_single_trace():
    df = pd.DataFrame({"amount": [1, 2, 3, 4]})

    fig = histogram(df, x="amount", nbins=2)

    assert len(fig.data) == 1
    assert fig.data[0].nbinsx == 2
    assert fig.layout.yaxis.title.text == "件数"


def test_histogram_with_color_overlays_one_trace_per_category():
    df = pd.DataFrame(
        {
            "amount": [1, 2, 3, 4],
            "seg": ["法人", "法人", "個人", "個人"],
        }
    )

    fig = histogram(df, x="amount", color="seg")

    assert [trace.name for trace in fig.data] == ["法人", "個人"]
    assert fig.layout.barmode == "overlay"
    assert all(trace.opacity == 0.6 for trace in fig.data)


def test_histogram_histnorm_is_forwarded_and_used_as_default_axis_title():
    df = pd.DataFrame({"amount": [1, 2, 3]})

    fig = histogram(df, x="amount", histnorm="percent")

    assert fig.data[0].histnorm == "percent"
    assert fig.layout.yaxis.title.text == "percent"
