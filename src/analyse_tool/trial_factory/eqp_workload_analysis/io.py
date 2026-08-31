"""eqp_workload_analysis の入出力（ファイルそのものの読み書き）。

4ステップ（prepare/process/analyze/visualize）の関数はファイルI/Oを
直接行わず、ここを経由してデータをやり取りする。
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from analyse_tool.common.output_index import register_output
from analyse_tool.common.profile import DatasetProfile, save_profile


def read_proc_history(input_path: str) -> duckdb.DuckDBPyRelation:
    """`proc_history`のParquetをDuckDBのリレーションとして読み込む。

    数百万行規模を想定し、pandasへ全件ロードしない。DuckDBのリレーション
    （遅延評価されるクエリ）のまま後続のステップに渡す。DuckDBの進捗バーは
    標準出力を汚すため無効化する。
    """
    con = duckdb.connect()
    con.execute("SET enable_progress_bar = false")
    path = Path(input_path)
    return con.sql(f"SELECT * FROM read_parquet('{path.as_posix()}')")


def write_profile(profile: DatasetProfile, profile_output_path: str) -> None:
    """前準備(EDA)で得た傾向プロファイルをJSONに保存する。"""
    save_profile(profile, profile_output_path)


def write_report_html(
    html: str,
    output_path: str,
    project_output_dir: str,
    note: str = "",
) -> None:
    """組み立て済みのレポートHTML文字列をファイルに書き出し、目次に登録する。"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    register_output(
        project_output_dir,
        tool_name="eqp_workload_analysis",
        output_path=path,
        note=note,
    )
