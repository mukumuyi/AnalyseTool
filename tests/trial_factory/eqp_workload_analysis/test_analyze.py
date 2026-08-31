import duckdb
import pandas as pd

from analyse_tool.trial_factory.eqp_workload_analysis.analyze import (
    aggregate_eqp_workload,
    build_hourly_utilization,
    build_lot_records,
    build_pareto,
)
from analyse_tool.trial_factory.eqp_workload_analysis.process import (
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
    # LOT001の2件目のみ待機時間30分を持つ（他は最初の工程でNULL、AVGはNULLを除外）
    assert result.loc["E1", "wait_total_minutes"] == 30
    assert result.loc["E1", "wait_avg_minutes"] == 30


def test_build_pareto_reuses_generic_pareto_data():
    workload_df = pd.DataFrame(
        {"eqp_id": ["E1", "E2", "E3"], "wait_total_minutes": [30, 100, 70]}
    )

    result = build_pareto(workload_df, top_n=2)

    assert list(result["eqp_id"]) == ["E2", "E3"]
    assert result["cum_pct"].iloc[-1] == 0.85  # 全体(200)に対する上位2件(170)の割合


def test_build_hourly_utilization_splits_busy_and_wait_minutes_within_each_hour():
    annotated = _annotated(
        [
            ("LOT001", "OP1", 1, "E1", "2026-01-01 00:00", "2026-01-01 00:30"),
        ]
    )
    period_start = pd.Timestamp("2026-01-01 00:00:00")
    period_end = pd.Timestamp("2026-01-01 02:00:00")

    result = build_hourly_utilization(annotated, ["E1"], period_start, period_end)

    first_hour = result[(result["hour_start"] == period_start)]
    busy_row = first_hour[first_hour["status"] == "着工中"].iloc[0]
    wait_row = first_hour[first_hour["status"] == "待機"].iloc[0]
    assert busy_row["minutes"] == 30
    assert wait_row["minutes"] == 30

    second_hour_start = period_start + pd.Timedelta(hours=1)
    second_hour = result[result["hour_start"] == second_hour_start]
    assert second_hour[second_hour["status"] == "着工中"].iloc[0]["minutes"] == 0
    assert second_hour[second_hour["status"] == "待機"].iloc[0]["minutes"] == 60


def test_build_hourly_utilization_hour_with_no_activity_is_fully_idle():
    # 回帰テスト: DuckDBのGREATEST/LEASTはNULL引数を無視するため、重なる行が
    # 無い時間帯をLEFT JOINで扱うと満稼働(60分)に化けるバグがあった。
    annotated = _annotated(
        [("LOT001", "OP1", 1, "E1", "2026-01-01 00:00", "2026-01-01 00:30")]
    )
    period_start = pd.Timestamp("2026-01-01 00:00:00")
    period_end = pd.Timestamp("2026-01-01 03:00:00")

    result = build_hourly_utilization(annotated, ["E1"], period_start, period_end)

    idle_hour = result[result["hour_start"] == period_start + pd.Timedelta(hours=1)]
    assert idle_hour[idle_hour["status"] == "着工中"].iloc[0]["minutes"] == 0
    assert idle_hour[idle_hour["status"] == "待機"].iloc[0]["minutes"] == 60


def test_build_hourly_utilization_start_count_aligns_with_the_offset_bucket_boundary():
    # 代表期間の開始時刻は分・秒付き（実データのMIN(start_time)）でも、
    # 着工件数の集計がバケット境界とずれずに数えられることを確認する
    # （date_trunc('hour', ...)とのミスマッチで常に0件になっていた不具合の回帰テスト）。
    annotated = _annotated(
        [
            ("LOT001", "OP1", 1, "E1", "2026-01-01 00:20:00", "2026-01-01 00:40:00"),
        ]
    )
    period_start = pd.Timestamp("2026-01-01 00:08:12.149103")
    period_end = period_start + pd.Timedelta(hours=2)

    result = build_hourly_utilization(annotated, ["E1"], period_start, period_end)

    first_hour = result[result["hour_start"] == period_start]
    assert first_hour[first_hour["status"] == "着工中"].iloc[0]["start_count"] == 1


def test_build_hourly_utilization_empty_eqp_ids_returns_empty_frame():
    annotated = _annotated(
        [("LOT001", "OP1", 1, "E1", "2026-01-01 00:00", "2026-01-01 00:30")]
    )

    result = build_hourly_utilization(
        annotated, [], pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02")
    )

    assert result.empty
    assert list(result.columns) == [
        "eqp_id",
        "hour_start",
        "status",
        "minutes",
        "start_count",
    ]


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

    # E1自身の行に加え、E1を出た直後(next_eqp_id=E9)の行(=E9側の行)も含む
    assert set(result["eqp_id"]) == {"E1", "E9"}


def test_build_lot_records_empty_eqp_ids_returns_empty_frame():
    annotated = _annotated(
        [("LOT001", "OP1", 1, "E1", "2026-01-01 00:00", "2026-01-01 00:30")]
    )

    result = build_lot_records(
        annotated, [], pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02")
    )

    assert result.empty
