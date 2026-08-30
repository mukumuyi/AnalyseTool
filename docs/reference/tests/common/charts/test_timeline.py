import pandas as pd

from analyse_tool.common.charts.timeline import timeline


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "task": ["T1", "T2", "T3"],
            "start": pd.to_datetime(["2026-01-01", "2026-01-03", "2026-01-02"]),
            "finish": pd.to_datetime(["2026-01-05", "2026-01-04", "2026-01-06"]),
            "phase": ["p1", "p2", "p1"],
        }
    )


def test_timeline_without_color_makes_a_single_horizontal_bar_trace():
    fig = timeline(_sample_df(), task="task", start="start", finish="finish")

    assert len(fig.data) == 1
    assert fig.data[0].orientation == "h"
    assert list(fig.data[0].y) == ["T1", "T2", "T3"]
    assert pd.Timestamp(fig.data[0].base[0]) == pd.Timestamp("2026-01-01")


def test_timeline_bar_length_is_the_duration_in_days():
    fig = timeline(_sample_df(), task="task", start="start", finish="finish")

    # T1: 2026-01-01 -> 2026-01-05 = 4日間
    # PlotlyのFigureはtimedeltaをナノ秒のintで保持するため、Timedeltaに戻して比較する。
    assert pd.Timedelta(fig.data[0].x[0]) == pd.Timedelta(days=4)


def test_timeline_with_color_groups_rows_by_category():
    fig = timeline(_sample_df(), task="task", start="start", finish="finish", color="phase")

    assert [trace.name for trace in fig.data] == ["p1", "p2"]
    assert list(fig.data[0].y) == ["T1", "T3"]
    assert list(fig.data[1].y) == ["T2"]
    assert sum(len(trace.y) for trace in fig.data) == 3


def test_timeline_y_axis_is_reversed_to_read_top_to_bottom():
    fig = timeline(_sample_df(), task="task", start="start", finish="finish")

    assert fig.layout.yaxis.autorange == "reversed"
