import pandas as pd

from analyse_tool.trial_factory.eqp_workload_fastview.visualize import (
    build_daily_index_payload,
    build_day_payload,
)


def test_build_daily_index_payload_formats_days_as_strings():
    df = pd.DataFrame(
        {
            "day": pd.date_range("2026-01-01", periods=2).date,
            "busy_minutes": [120, 0],
            "start_count": [4, 0],
            "utilization_pct": [12.345, 0.0],
        }
    )

    payload = build_daily_index_payload(df)

    assert payload["days"] == ["2026-01-01", "2026-01-02"]
    assert payload["utilization_pct"] == [12.35, 0.0]
    assert payload["start_count"] == [4, 0]


def test_build_day_payload_computes_minutes_from_day_start():
    day_start = pd.Timestamp("2026-03-01")
    segments_df = pd.DataFrame(
        {
            "eqp_id": ["E1"],
            "lot_id": ["LOT001"],
            "start_time": [pd.Timestamp("2026-03-01 08:00")],
            "end_time": [pd.Timestamp("2026-03-01 09:30")],
            "lane": [0],
        }
    )
    wip_df = pd.DataFrame(
        {
            "t": [pd.Timestamp("2026-03-01 08:00"), pd.Timestamp("2026-03-01 08:15")],
            "busy": [1, 1],
            "wait": [0, 0],
        }
    )
    lot_detail_df = pd.DataFrame(
        {
            "lot_id": ["LOT001"],
            "prodspec_id": ["PS01"],
            "mainpd_id": ["MP01"],
            "ope_no": ["OP1"],
            "ope_seq": [1],
            "eqp_id": ["E1"],
            "start_time": [pd.Timestamp("2026-03-01 08:00")],
            "end_time": [pd.Timestamp("2026-03-01 09:30")],
            "wait_minutes": [None],
            "prev_eqp_id": [None],
            "next_eqp_id": [None],
        }
    )

    payload = build_day_payload(
        "2026-03-01", segments_df, wip_df, lot_detail_df, ["E1", "E2"], day_start
    )

    assert payload["date"] == "2026-03-01"
    assert payload["eqp_ids"] == ["E1", "E2"]
    assert payload["segments"]["start_min"] == [480.0]  # 08:00 = 480分
    assert payload["segments"]["end_min"] == [570.0]  # 09:30 = 570分
    assert payload["wip"]["t_min"] == [480.0, 495.0]
    assert payload["lot_detail"]["data"]["start_time"] == ["2026-03-01T08:00:00"]
    assert payload["lot_detail"]["columns"][0] == "lot_id"


def test_build_day_payload_handles_empty_frames():
    day_start = pd.Timestamp("2026-03-01")
    empty_segments = pd.DataFrame(
        columns=["eqp_id", "lot_id", "start_time", "end_time", "lane"]
    )
    empty_wip = pd.DataFrame(columns=["t", "busy", "wait"])
    empty_lot_detail = pd.DataFrame(
        columns=[
            "lot_id",
            "prodspec_id",
            "mainpd_id",
            "ope_no",
            "ope_seq",
            "eqp_id",
            "start_time",
            "end_time",
            "wait_minutes",
            "prev_eqp_id",
            "next_eqp_id",
        ]
    )

    payload = build_day_payload(
        "2026-03-01", empty_segments, empty_wip, empty_lot_detail, [], day_start
    )

    assert payload["segments"]["eqp_id"] == []
    assert payload["wip"]["busy"] == []
    assert payload["lot_detail"]["data"]["lot_id"] == []
