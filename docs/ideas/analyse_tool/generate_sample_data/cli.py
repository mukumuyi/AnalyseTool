"""generate_sample_data の引数定義。"""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_sample_data",
        description=(
            "データ定義情報（プロファイルJSON）を元に、サンプルデータを"
            "Parquetファイルとして生成する。"
        ),
    )
    parser.add_argument(
        "--profile",
        required=True,
        help=(
            "データ定義情報（プロファイル）のJSONファイルパス。"
            "prepare.py の出力、または profiles/ 配下の定義ファイルを指定する。"
        ),
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        help="生成する行数。省略時はプロファイルの row_count をそのまま使う。",
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
        help="出力先Parquetファイルパス（例: output/orders_sample.parquet）。",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)
