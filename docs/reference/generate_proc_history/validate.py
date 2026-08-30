"""生成結果`proc_history`が、決めた生成ルールを守っているかの自動検証。

`generate.py`が組み立てた`pyarrow.Table`をそのままDuckDBに登録し、SQLで
ルール違反の有無を確認する。「テーブルを受け取り、違反内容の説明文リスト
を返す（空なら問題無し）」という純粋関数として実装し、`__init__.py`の
`main()`がParquet書き出し前に呼び出す。
"""

from __future__ import annotations

import duckdb
import pyarrow as pa


def validate_table(table: pa.Table) -> list[str]:
    """生成ルールを検証し、違反内容の説明文リストを返す（空なら問題無し）。"""
    con = duckdb.connect()
    con.register("proc_history", table)
    try:
        violations: list[str] = []
        violations += _check_start_before_end(con)
        violations += _check_ope_seq_sequential(con)
        violations += _check_monotonic_between_operations(con)
        violations += _check_fixed_eqp_duration(con)
        violations += _check_mainpd_prodspec_consistency(con)
        return violations
    finally:
        con.close()


def _check_start_before_end(con: duckdb.DuckDBPyConnection) -> list[str]:
    """全行で`start_time < end_time`が成り立つことを確認する。"""
    row = con.sql(
        "SELECT COUNT(*) FROM proc_history WHERE start_time >= end_time"
    ).fetchone()
    assert row is not None
    n = row[0]
    if n:
        return [
            f"start_time >= end_time の行が{n}件あります（start_time < end_timeであるべき）"
        ]
    return []


def _check_ope_seq_sequential(con: duckdb.DuckDBPyConnection) -> list[str]:
    """ロットごとに`ope_seq`が1から欠番・重複なく連番になっていることを確認する。"""
    bad = con.sql(
        """
        SELECT lot_id
        FROM proc_history
        GROUP BY lot_id
        HAVING
            MIN(ope_seq) <> 1
            OR MAX(ope_seq) <> COUNT(*)
            OR COUNT(DISTINCT ope_seq) <> COUNT(*)
        LIMIT 5
        """
    ).fetchall()
    if bad:
        examples = ", ".join(row[0] for row in bad)
        return [f"ope_seqが1からの連番になっていないロットがあります（例: {examples}）"]
    return []


def _check_monotonic_between_operations(con: duckdb.DuckDBPyConnection) -> list[str]:
    """同一ロット内で、工程N+1のstart_timeが工程Nのend_timeより後ろであることを確認する。"""
    row = con.sql(
        """
        WITH ordered AS (
            SELECT
                lot_id,
                start_time,
                LAG(end_time) OVER (PARTITION BY lot_id ORDER BY ope_seq) AS prev_end_time
            FROM proc_history
        )
        SELECT COUNT(*)
        FROM ordered
        WHERE prev_end_time IS NOT NULL AND start_time <= prev_end_time
        """
    ).fetchone()
    assert row is not None
    n = row[0]
    if n:
        message = f"前工程のend_time以前にstart_timeが来ている行が{n}件あります（次工程は前工程より後ろに開始するべき）"
        return [message]
    return []


def _check_fixed_eqp_duration(con: duckdb.DuckDBPyConnection) -> list[str]:
    """同じ`eqp_id`を使った行の処理時間（end_time - start_time）が常に一定であることを確認する。"""
    bad = con.sql(
        """
        SELECT eqp_id
        FROM proc_history
        GROUP BY eqp_id
        HAVING COUNT(DISTINCT end_time - start_time) > 1
        LIMIT 5
        """
    ).fetchall()
    if bad:
        examples = ", ".join(row[0] for row in bad)
        return [
            f"処理時間が設備ごとに一定になっていないeqp_idがあります（例: {examples}）"
        ]
    return []


def _check_mainpd_prodspec_consistency(con: duckdb.DuckDBPyConnection) -> list[str]:
    """`mainpd_id`が常に同じ`prodspec_id`に紐づいていることを確認する。"""
    bad = con.sql(
        """
        SELECT mainpd_id
        FROM proc_history
        GROUP BY mainpd_id
        HAVING COUNT(DISTINCT prodspec_id) > 1
        LIMIT 5
        """
    ).fetchall()
    if bad:
        examples = ", ".join(row[0] for row in bad)
        return [f"複数のprodspec_idに紐づいているmainpd_idがあります（例: {examples}）"]
    return []
