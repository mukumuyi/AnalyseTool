import duckdb
import pandas as pd

from analyse_tool.trial_factory.eqp_workload_fastview.analyze import (
    aggregate_daily_index,
    aggregate_eqp_workload,
    assign_lanes_to_segments,
    assign_sublanes,
    build_day_segments,
    build_day_wip_series,
    build_lot_records,
    build_pareto,
)
from analyse_tool.trial_factory.eqp_workload_fastview.process import (
    annotate_lot_sequence,
    clean_proc_history,
)


def _annotated(rows: list[tuple]) -> duckdb.DuckDBPyRelation:
    con = duckdb.connect()
    values = ", ".join(
        f"('{lot}', 'PS01', 'MP01', '{ope}', {seq}, '{eqp}', "
        f"TIMESTAMP '{start}', TIMESTAMP '{end}')"
        for lot, ope, seq, eqp, start, end in rows
    )
    raw = con.sql(
        f"SELECT * FROM (VALUES {values}) "
        "AS t(lot_id, prodspec_id, mainpd_id, ope_no, ope_seq, eqp_id, start_time, end_time)"
    )
    return annotate_lot_sequence(clean_proc_history(raw))


def test_aggregate_eqp_workload_computes_count_and_wait_stats():
    annotated = _annotated(
        [
            ("LOT001", "OP1", 1, "E1", "2026-01-01 00:00", "2026-01-01 01:00"),
            ("LOT001", "OP2", 2, "E1", "2026-01-01 01:30", "2026-01-01 02:00"),
            ("LOT002", "OP1", 1, "E1", "2026-01-01 03:00", "2026-01-01 03:30"),
        ]
    )

    result = aggregate_eqp_workload(annotated).set_index("eqp_id")

    assert result.loc["E1", "proc_count"] == 3
    assert result.loc["E1", "wait_total_minutes"] == 30
    assert result.loc["E1", "wait_avg_minutes"] == 30


def test_build_pareto_reuses_generic_pareto_data():
    workload_df = pd.DataFrame(
        {"eqp_id": ["E1", "E2", "E3"], "wait_total_minutes": [30, 100, 70]}
    )

    result = build_pareto(workload_df, top_n=2)

    assert list(result["eqp_id"]) == ["E2", "E3"]
    assert result["cum_pct"].iloc[-1] == 0.85


def test_aggregate_daily_index_fills_idle_days_with_zero():
    annotated = _annotated(
        [
            ("LOT001", "OP1", 1, "E1", "2026-01-01 00:00", "2026-01-01 01:00"),
            ("LOT001", "OP2", 2, "E1", "2026-01-03 00:00", "2026-01-03 00:30"),
        ]
    )

    result = aggregate_daily_index(annotated, ["E1"]).set_index("day")

    assert list(result.index.astype(str)) == ["2026-01-01", "2026-01-02", "2026-01-03"]
    assert result.loc[pd.Timestamp("2026-01-02").date(), "busy_minutes"] == 0
    assert result.loc[pd.Timestamp("2026-01-02").date(), "start_count"] == 0
    assert result.loc[pd.Timestamp("2026-01-01").date(), "busy_minutes"] == 60
    # 1台×24時間=1440分に対する60分の稼働率
    assert (
        result.loc[pd.Timestamp("2026-01-01").date(), "utilization_pct"]
        == 60 / 1440 * 100
    )


def test_aggregate_daily_index_empty_eqp_ids_returns_empty_frame():
    annotated = _annotated(
        [("LOT001", "OP1", 1, "E1", "2026-01-01 00:00", "2026-01-01 00:30")]
    )

    result = aggregate_daily_index(annotated, [])

    assert result.empty
    assert list(result.columns) == [
        "day",
        "busy_minutes",
        "start_count",
        "utilization_pct",
    ]


def test_build_day_segments_clips_to_day_boundary():
    annotated = _annotated(
        [
            # 前日23:00開始、当日01:00終了 → 当日分は00:00始まりへクリップされる
            ("LOT001", "OP1", 1, "E1", "2026-01-01 23:00", "2026-01-02 01:00"),
        ]
    )
    day_start = pd.Timestamp("2026-01-02 00:00:00")
    day_end = pd.Timestamp("2026-01-03 00:00:00")

    result = build_day_segments(annotated, ["E1"], day_start, day_end)

    assert len(result) == 1
    assert result.iloc[0]["start_time"] == day_start
    assert result.iloc[0]["end_time"] == pd.Timestamp("2026-01-02 01:00:00")


def test_build_day_segments_empty_eqp_ids_returns_empty_frame():
    annotated = _annotated(
        [("LOT001", "OP1", 1, "E1", "2026-01-01 00:00", "2026-01-01 00:30")]
    )

    result = build_day_segments(
        annotated, [], pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02")
    )

    assert result.empty
    assert list(result.columns) == ["eqp_id", "lot_id", "start_time", "end_time"]


def test_assign_sublanes_no_overlap_reuses_single_lane():
    segments = [
        (pd.Timestamp("2026-01-01 00:00"), pd.Timestamp("2026-01-01 01:00")),
        (pd.Timestamp("2026-01-01 01:00"), pd.Timestamp("2026-01-01 02:00")),
    ]

    assert assign_sublanes(segments) == [0, 0]


def test_assign_sublanes_full_overlap_needs_separate_lanes():
    segments = [
        (pd.Timestamp("2026-01-01 00:00"), pd.Timestamp("2026-01-01 02:00")),
        (pd.Timestamp("2026-01-01 00:30"), pd.Timestamp("2026-01-01 01:30")),
        (pd.Timestamp("2026-01-01 00:45"), pd.Timestamp("2026-01-01 01:00")),
    ]

    result = assign_sublanes(segments)

    assert len(set(result)) == 3


def test_assign_sublanes_reuses_freed_lane():
    # E1: 0:00-1:00 (lane0), E2: 0:30-0:45 (lane1, E1と重なる),
    # E3: 1:00-2:00 (E1終了後なのでlane0を再利用できるはず)
    segments = [
        (pd.Timestamp("2026-01-01 00:00"), pd.Timestamp("2026-01-01 01:00")),
        (pd.Timestamp("2026-01-01 00:30"), pd.Timestamp("2026-01-01 00:45")),
        (pd.Timestamp("2026-01-01 01:00"), pd.Timestamp("2026-01-01 02:00")),
    ]

    result = assign_sublanes(segments)

    assert result[0] == result[2]
    assert result[1] != result[0]


def test_assign_sublanes_empty_returns_empty():
    assert assign_sublanes([]) == []


def test_assign_lanes_to_segments_assigns_within_each_equipment_independently():
    segments_df = pd.DataFrame(
        {
            "eqp_id": ["E1", "E1", "E2"],
            "lot_id": ["L1", "L2", "L3"],
            "start_time": [
                pd.Timestamp("2026-01-01 00:00"),
                pd.Timestamp("2026-01-01 00:30"),
                pd.Timestamp("2026-01-01 00:00"),
            ],
            "end_time": [
                pd.Timestamp("2026-01-01 01:00"),
                pd.Timestamp("2026-01-01 01:00"),
                pd.Timestamp("2026-01-01 01:00"),
            ],
        }
    )

    result = assign_lanes_to_segments(segments_df)

    e1_lanes = set(result[result["eqp_id"] == "E1"]["lane"])
    e2_lanes = set(result[result["eqp_id"] == "E2"]["lane"])
    assert e1_lanes == {0, 1}
    # E2はE1と設備が違うため、E1のレーン割当に影響されず0番から独立して割り当たる
    assert e2_lanes == {0}


def test_assign_lanes_to_segments_empty_returns_empty_with_lane_column():
    result = assign_lanes_to_segments(
        pd.DataFrame(columns=["eqp_id", "lot_id", "start_time", "end_time"])
    )

    assert result.empty
    assert "lane" in result.columns


def test_build_day_wip_series_counts_busy_and_wait():
    annotated = _annotated(
        [
            # 前工程(E5)が07:00-07:30に終了し、E1への着工が08:00
            # → wait_minutes=30、07:30-08:00が着工待ち
            ("LOT001", "OP0", 1, "E5", "2026-01-01 07:00", "2026-01-01 07:30"),
            ("LOT001", "OP1", 2, "E1", "2026-01-01 08:00", "2026-01-01 08:30"),
            # E1を出た直後E9へ、09:00開始 → E1終了(08:30)〜E9開始(09:00)が待機
            ("LOT001", "OP2", 3, "E9", "2026-01-01 09:00", "2026-01-01 09:30"),
        ]
    )
    day_start = pd.Timestamp("2026-01-01 00:00:00")
    day_end = pd.Timestamp("2026-01-02 00:00:00")

    result = build_day_wip_series(annotated, ["E1"], day_start, day_end).set_index("t")

    assert result.loc[pd.Timestamp("2026-01-01 07:45"), "wait"] == 1
    assert result.loc[pd.Timestamp("2026-01-01 08:15"), "busy"] == 1
    assert result.loc[pd.Timestamp("2026-01-01 08:45"), "wait"] == 1
    assert result.loc[pd.Timestamp("2026-01-01 12:00"), "busy"] == 0
    assert len(result) == 96


def test_build_day_wip_series_does_not_double_count_transfer_between_two_target_eqp():
    # 対象設備群がE1・E2の両方を含む場合、E1終了(08:30)からE2着工(09:00)
    # までの待機は1件としてのみ数える（旧実装ではE1側の退出待ち・E2側の
    # 着工待ちの両方に計上され、合計が実際のロット数より多くなっていた）。
    annotated = _annotated(
        [
            ("LOT001", "OP1", 1, "E1", "2026-01-01 08:00", "2026-01-01 08:30"),
            ("LOT001", "OP2", 2, "E2", "2026-01-01 09:00", "2026-01-01 09:30"),
        ]
    )
    day_start = pd.Timestamp("2026-01-01 00:00:00")
    day_end = pd.Timestamp("2026-01-02 00:00:00")

    result = build_day_wip_series(
        annotated, ["E1", "E2"], day_start, day_end
    ).set_index("t")
    row = result.loc[pd.Timestamp("2026-01-01 08:45")]

    assert row["wait"] == 1
    assert row["busy"] + row["wait"] == 1  # LOT001は1件のみ


def test_build_day_wip_series_empty_eqp_ids_returns_empty_frame():
    annotated = _annotated(
        [("LOT001", "OP1", 1, "E1", "2026-01-01 00:00", "2026-01-01 00:30")]
    )

    result = build_day_wip_series(
        annotated, [], pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02")
    )

    assert result.empty
    assert list(result.columns) == ["t", "busy", "wait"]


def test_build_lot_records_includes_boundary_rows_at_other_equipment():
    annotated = _annotated(
        [
            ("LOT001", "OP1", 1, "E1", "2026-01-01 00:00", "2026-01-01 01:00"),
            ("LOT001", "OP2", 2, "E9", "2026-01-01 01:30", "2026-01-01 02:00"),
        ]
    )
    period_start = pd.Timestamp("2026-01-01 00:00:00")
    period_end = pd.Timestamp("2026-01-01 03:00:00")

    result = build_lot_records(annotated, ["E1"], period_start, period_end)

    assert set(result["eqp_id"]) == {"E1", "E9"}


def test_build_lot_records_empty_eqp_ids_returns_empty_frame():
    annotated = _annotated(
        [("LOT001", "OP1", 1, "E1", "2026-01-01 00:00", "2026-01-01 00:30")]
    )

    result = build_lot_records(
        annotated, [], pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02")
    )

    assert result.empty
