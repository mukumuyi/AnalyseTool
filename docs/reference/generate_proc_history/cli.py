"""generate_proc_history の引数定義。"""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_proc_history",
        description=(
            "proc_history生成用の設定JSON（ProcHistoryConfig）を元に、"
            "工程実績履歴のサンプルデータをParquetファイルとして生成する。"
        ),
    )
    parser.add_argument(
        "--config",
        required=True,
        help="proc_history生成用の設定JSONファイルパス（例: profiles/proc_history_config.json）。",
    )
    parser.add_argument(
        "--lot-count",
        type=int,
        default=None,
        help="生成するロット数。省略時は設定ファイルのlot_countをそのまま使う。",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="乱数シード（既定: 0）。同じ値を指定すれば同じデータを再現できる。",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="出力先Parquetファイルパス（例: output/proc_history_sample.parquet）。",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)
