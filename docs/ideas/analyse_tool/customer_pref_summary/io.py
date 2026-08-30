"""customer_pref_summary の入出力（ファイルそのものの読み書き）。

4ステップ（prepare/process/analyze/visualize）の関数はファイルI/Oを
直接行わず、ここを経由してデータをやり取りする。
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from analyse_tool.common.profile import DatasetProfile, save_profile


def read_customers(input_path: str) -> duckdb.DuckDBPyRelation:
    """顧客マスタのParquetをDuckDBのリレーションとして読み込む。

    件数が多くても全件をpandasにロードしないよう、DuckDBのリレーション
    （遅延評価されるクエリ）のまま後続のステップに渡す。
    """
    path = Path(input_path)
    return duckdb.sql(f"SELECT * FROM read_parquet('{path.as_posix()}')")


def write_profile(profile: DatasetProfile, profile_output_path: str) -> None:
    """前準備(EDA)で得た傾向プロファイルをJSONに保存する。"""
    save_profile(profile, profile_output_path)


def write_report_html(html: str, output_path: str) -> None:
    """組み立て済みのレポートHTML文字列をファイルに書き出す。"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
