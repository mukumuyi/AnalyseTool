import pandas as pd

from analyse_tool.common.charts.barline import bar_with_line


def test_bar_with_line_single_series_puts_line_on_secondary_axis():
    df = pd.DataFrame(
        {
            "eqp_id": ["E1", "E2"],
            "wait_total": [100, 50],
            "cum_pct": [0.67, 1.0],
        }
    )

    fig = bar_with_line(df, x="eqp_id", y_bar="wait_total", y_line="cum_pct")

    assert len(fig.data) == 2
    bar_trace, line_trace = fig.data
    assert bar_trace.type == "bar"
    assert line_trace.type == "scatter"
    assert line_trace.yaxis == "y2"
    assert list(line_trace.y) == [0.67, 1.0]


def test_bar_with_line_color_creates_stacked_bars_plus_one_line():
    df = pd.DataFrame(
        {
            "hour": [1, 1, 2, 2],
            "status": ["busy", "wait", "busy", "wait"],
            "n": [3, 1, 2, 2],
            "start_count": [5, 5, 4, 4],
        }
    )

    fig = bar_with_line(df, x="hour", y_bar="n", y_line="start_count", color="status")

    assert len(fig.data) == 3  # 2色 + 折れ線1本
    assert fig.data[-1].type == "scatter"
    # 折れ線はhourごとに重複排除した1点ずつ
    assert list(fig.data[-1].y) == [5, 4]
