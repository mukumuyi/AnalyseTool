"""eqp_workload_fastview の入出力（ファイルそのものの読み書き）。

4ステップ（prepare/process/analyze/visualize）の関数はファイルI/Oを
直接行わず、ここを経由してデータをやり取りする。

旧版`eqp_workload_analysis`の単一HTML出力と異なり、本ツールは
「シェルHTML＋日次インデックス＋日別JSON」というディレクトリを書き出す
（`.steering/20260901-eqp-workload-fastview/design.md`の「対象／構成物
一覧」参照）。書き込み中の異常終了で壊れたファイルが残らないよう、
各ファイルは一時ファイル→`os.replace()`で確定させる。
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import duckdb

from analyse_tool.common.output_index import register_output
from analyse_tool.common.profile import DatasetProfile, save_profile

DAYS_DIR_NAME = "days"
DATA_DIR_NAME = "data"
DAILY_INDEX_FILENAME = "daily_index.json"
INDEX_HTML_FILENAME = "index.html"


def read_proc_history(
    input_path: str,
) -> tuple[duckdb.DuckDBPyConnection, duckdb.DuckDBPyRelation]:
    """`proc_history`のParquetをDuckDBのリレーションとして読み込む。

    数百万行規模を想定し、pandasへ全件ロードしない。DuckDBのリレーション
    （遅延評価されるクエリ）のまま後続のステップに渡す。DuckDBの進捗バーは
    標準出力を汚すため無効化する。

    接続（`duckdb.DuckDBPyConnection`）もあわせて返す。⑥-3/⑥-4は日ごとに
    何度も同じ加工済みリレーションへ問い合わせるため、`process.materialize()`
    で実テーブル化する際にこの接続が必要になる。
    """
    con = duckdb.connect()
    con.execute("SET enable_progress_bar = false")
    path = Path(input_path)
    return con, con.sql(f"SELECT * FROM read_parquet('{path.as_posix()}')")


def write_profile(profile: DatasetProfile, profile_output_path: str) -> None:
    """前準備(EDA)で得た傾向プロファイルをJSONに保存する。"""
    save_profile(profile, profile_output_path)


def write_fastview_report(
    *,
    output_dir: str,
    shell_html: str,
    daily_index_payload: dict[str, Any],
    day_payloads: dict[str, dict[str, Any]],
    project_output_dir: str,
    note: str = "",
) -> Path:
    """シェルHTML・日次インデックス・日別JSONを出力ディレクトリへ安全に書き出す。

    Args:
        output_dir: このレポート専用の出力ディレクトリ
            （例: `output/trial_factory/<実行日>/eqp_workload_fastview_<時刻>/`）。
        shell_html: `index.html`の中身。
        daily_index_payload: ⑥-2用の日次インデックス（⑥-2は全期間分を
            シェルHTMLへ直接埋め込むため、ここではデバッグ・再利用向けに
            `data/daily_index.json`としても書き出す）。
        day_payloads: `{"YYYY-MM-DD": ⑥-3/⑥-4用のペイロード}`。
            高速モードは日クリック時にこれを1件ずつ`fetch()`する。
        project_output_dir: `output/<プロジェクト名>/`のパス
            （`register_output()`への登録先）。
        note: 目次（`output/<プロジェクト名>/index.html`）に残す備考。

    Returns:
        書き出した`index.html`のパス。
    """
    out_dir = Path(output_dir)
    data_dir = out_dir / DATA_DIR_NAME
    days_dir = data_dir / DAYS_DIR_NAME
    days_dir.mkdir(parents=True, exist_ok=True)

    index_path = out_dir / INDEX_HTML_FILENAME
    _write_text_atomically(index_path, shell_html)
    _write_json_atomically(data_dir / DAILY_INDEX_FILENAME, daily_index_payload)
    for day, payload in day_payloads.items():
        _write_json_atomically(days_dir / f"{day}.json", payload)

    register_output(
        project_output_dir,
        tool_name="eqp_workload_fastview",
        output_path=index_path,
        note=note,
    )
    return index_path


def _write_text_atomically(path: Path, content: str) -> None:
    """一時ファイルに書いてから`os.replace()`でリネームする（安全な書き込み）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except BaseException:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def _write_json_atomically(path: Path, payload: dict[str, Any]) -> None:
    _write_text_atomically(path, json.dumps(payload, ensure_ascii=False, default=str))
