import pandas as pd

from analyse_tool.common.charts.twograph import GANTT_CURVE_NUMBER, gantt_and_wip_chart


def _gantt_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "lane": [0, 1],
            "start": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:30"]),
            "end": pd.to_datetime(["2026-01-01 01:00", "2026-01-01 01:15"]),
            "lot_id": ["LOT001", "LOT002"],
            "status": ["busy", "busy"],
        }
    )


def _wip_df() -> pd.DataFrame:
    hours = pd.to_datetime(["2026-01-01 00:00", "2026-01-01 01:00"] * 3)
    return pd.DataFrame(
        {
            "t": hours,
            "cat": ["busy"] * 2 + ["wait_self"] * 2 + ["wait_other"] * 2,
            "n": [1, 2, 0, 1, 0, 0],
        }
    )


def _build_fig():
    return gantt_and_wip_chart(
        _gantt_df(),
        _wip_df(),
        gantt_start="start",
        gantt_end="end",
        gantt_lane="lane",
        gantt_label="lot_id",
        gantt_color="status",
        wip_x="t",
        wip_y="n",
        wip_color="cat",
    )


def test_gantt_trace_is_always_added_first_at_the_fixed_curve_number():
    fig = _build_fig()

    assert fig.data[GANTT_CURVE_NUMBER].type == "bar"
    assert GANTT_CURVE_NUMBER == 0


def test_wip_traces_follow_the_gantt_trace_and_land_on_the_second_row():
    fig = _build_fig()

    wip_traces = fig.data[1:]
    assert len(wip_traces) == 3
    assert all(trace.type == "scatter" for trace in wip_traces)
    assert all(trace.yaxis == "y2" for trace in wip_traces)


def test_xaxes_are_shared_between_the_two_rows():
    fig = _build_fig()

    assert fig.layout.xaxis.matches == "x2"
