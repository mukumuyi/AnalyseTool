import pandas as pd

from analyse_tool.trial_factory.eqp_workload_analysis.visualize import (
    _build_stage3_placeholder,
    _default_hour,
    _lot_detail_to_columnar,
)


def test_lot_detail_to_columnar_formats_datetimes_as_iso8601():
    df = pd.DataFrame(
        {
            "lot_id": ["LOT001"],
            "start_time": pd.to_datetime(["2026-01-01 05:08:12.149103"]),
            "end_time": pd.to_datetime(["2026-01-01 05:38:12.149103"]),
        }
    )

    columns, data = _lot_detail_to_columnar(df)

    assert columns == ["lot_id", "start_time", "end_time"]
    assert data["start_time"][0] == "2026-01-01T05:08:12.149103"
    assert data["lot_id"][0] == "LOT001"


def test_lot_detail_to_columnar_converts_missing_values_to_none():
    df = pd.DataFrame(
        {
            "lot_id": ["LOT001", "LOT002"],
            "prev_eqp_id": ["E1", None],
            "start_time": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 01:00"]),
            "end_time": pd.to_datetime(["2026-01-01 00:30", "2026-01-01 01:30"]),
        }
    )

    _, data = _lot_detail_to_columnar(df)

    assert data["prev_eqp_id"] == ["E1", None]


def test_default_hour_picks_the_busiest_hour_when_activity_exists():
    hourly = pd.DataFrame(
        {
            "eqp_id": ["E1", "E1", "E1", "E1"],
            "hour_start": pd.to_datetime(
                [
                    "2026-01-01 00:00",
                    "2026-01-01 00:00",
                    "2026-01-01 01:00",
                    "2026-01-01 01:00",
                ]
            ),
            "status": ["着工中", "待機", "着工中", "待機"],
            "minutes": [5, 55, 50, 10],
        }
    )

    result = _default_hour(hourly, "E1")

    assert result == pd.Timestamp("2026-01-01 01:00")


def test_default_hour_falls_back_to_the_first_hour_when_fully_idle():
    hourly = pd.DataFrame(
        {
            "eqp_id": ["E1", "E1"],
            "hour_start": pd.to_datetime(["2026-01-02 00:00", "2026-01-01 00:00"]),
            "status": ["着工中", "着工中"],
            "minutes": [0, 0],
        }
    )

    result = _default_hour(hourly, "E1")

    assert result == pd.Timestamp("2026-01-01 00:00")


def test_stage3_placeholder_has_the_same_trace_shape_as_a_real_render():
    fig = _build_stage3_placeholder()

    assert [t.type for t in fig.data] == ["bar", "scatter", "scatter", "scatter"]
    assert fig.layout.xaxis.type == "date"
