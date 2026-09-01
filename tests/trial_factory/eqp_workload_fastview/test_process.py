import duckdb
import pandas as pd

from analyse_tool.trial_factory.eqp_workload_fastview.process import (
    annotate_lot_sequence,
    clean_proc_history,
    materialize,
)


def _relation(rows: list[dict]) -> duckdb.DuckDBPyRelation:
    con = duckdb.connect()
    return con.sql(
        "SELECT * FROM (VALUES " + ", ".join(_row_sql(r) for r in rows) + ") "
        "AS t(lot_id, prodspec_id, mainpd_id, ope_no, ope_seq, eqp_id, start_time, end_time)"
    )


def _row_sql(row: dict) -> str:
    return (
        f"('{row['lot_id']}', 'PS01', 'MP01', '{row['ope_no']}', {row['ope_seq']}, "
        f"'{row['eqp_id']}', TIMESTAMP '{row['start_time']}', TIMESTAMP '{row['end_time']}')"
    )


def test_clean_proc_history_drops_rows_missing_required_columns():
    con = duckdb.connect()
    raw = con.sql(
        """
        SELECT * FROM (VALUES
            ('LOT001', 'PS01', 'MP01', 'OP1', 1, 'E1', TIMESTAMP '2026-01-01 00:00', TIMESTAMP '2026-01-01 01:00'),
            (NULL,     'PS01', 'MP01', 'OP1', 1, 'E1', TIMESTAMP '2026-01-01 00:00', TIMESTAMP '2026-01-01 01:00'),
            ('LOT003', 'PS01', 'MP01', 'OP1', 1, NULL,  TIMESTAMP '2026-01-01 00:00', TIMESTAMP '2026-01-01 01:00')
        ) AS t(lot_id, prodspec_id, mainpd_id, ope_no, ope_seq, eqp_id, start_time, end_time)
        """
    )

    result = clean_proc_history(raw).df()

    assert len(result) == 1
    assert result["lot_id"].tolist() == ["LOT001"]


def test_annotate_lot_sequence_computes_wait_minutes_from_previous_step_end_time():
    raw = _relation(
        [
            {
                "lot_id": "LOT001",
                "ope_no": "OP1",
                "ope_seq": 1,
                "eqp_id": "E1",
                "start_time": "2026-01-01 00:00:00",
                "end_time": "2026-01-01 01:00:00",
            },
            {
                "lot_id": "LOT001",
                "ope_no": "OP2",
                "ope_seq": 2,
                "eqp_id": "E2",
                "start_time": "2026-01-01 01:30:00",
                "end_time": "2026-01-01 02:00:00",
            },
        ]
    )

    result = annotate_lot_sequence(clean_proc_history(raw)).df().sort_values("ope_seq")

    assert result.iloc[1]["wait_minutes"] == 30
    assert result.iloc[1]["prev_eqp_id"] == "E1"
    assert result.iloc[0]["next_eqp_id"] == "E2"


def test_annotate_lot_sequence_boundary_rows_have_null_prev_and_next():
    raw = _relation(
        [
            {
                "lot_id": "LOT001",
                "ope_no": "OP1",
                "ope_seq": 1,
                "eqp_id": "E1",
                "start_time": "2026-01-01 00:00:00",
                "end_time": "2026-01-01 01:00:00",
            },
            {
                "lot_id": "LOT001",
                "ope_no": "OP2",
                "ope_seq": 2,
                "eqp_id": "E2",
                "start_time": "2026-01-01 01:30:00",
                "end_time": "2026-01-01 02:00:00",
            },
        ]
    )

    result = annotate_lot_sequence(clean_proc_history(raw)).df().sort_values("ope_seq")

    first_row, last_row = result.iloc[0], result.iloc[1]
    assert pd.isna(first_row["prev_eqp_id"])
    assert pd.isna(first_row["wait_minutes"])
    assert pd.isna(last_row["next_eqp_id"])


def _annotated_on(con: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyRelation:
    raw = con.sql(
        "SELECT * FROM (VALUES "
        "('LOT001', 'PS01', 'MP01', 'OP1', 1, 'E1', "
        "TIMESTAMP '2026-01-01 00:00', TIMESTAMP '2026-01-01 01:00')"
        ") AS t(lot_id, prodspec_id, mainpd_id, ope_no, ope_seq, eqp_id, start_time, end_time)"
    )
    return annotate_lot_sequence(clean_proc_history(raw))


def test_materialize_returns_an_equivalent_but_physical_relation():
    con = duckdb.connect()
    annotated = _annotated_on(con)

    materialized = materialize(con, annotated)

    assert materialized.aggregate("COUNT(*)").fetchone()[0] == 1
    # 実テーブル化後も同じ内容を返し続けること（何度問い合わせても同じ結果）
    assert materialized.aggregate("COUNT(*)").fetchone()[0] == 1
    assert list(materialized.df()["eqp_id"]) == ["E1"]


def test_materialize_can_be_called_again_on_the_same_connection():
    con = duckdb.connect()
    annotated = _annotated_on(con)

    materialize(con, annotated)
    second = materialize(con, annotated)  # 既存テーブルがあってもエラーにならない

    assert second.aggregate("COUNT(*)").fetchone()[0] == 1
