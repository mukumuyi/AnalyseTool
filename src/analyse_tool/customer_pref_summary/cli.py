"""customer_pref_summary の引数定義。"""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="customer_pref_summary",
        description=(
            "顧客マスタ（customers）を地方区分(pref)ごとに集計し、"
            "顧客区分(segment)で色分けした棒グラフのインタラクティブレポートを作る。"
        ),
    )
    parser.add_argument(
        "--input",
        default="output/customers_sample.parquet",
        help="顧客マスタのParquetファイルパス（既定: output/customers_sample.parquet）。",
    )
    parser.add_argument(
        "--output",
        default="output/customer_pref_summary.html",
        help="出力するレポートHTMLのパス（既定: output/customer_pref_summary.html）。",
    )
    parser.add_argument(
        "--profile-output",
        default="output/customer_pref_summary_profile.json",
        help=(
            "前準備(EDA)で作る傾向プロファイルJSONの出力パス"
            "（既定: output/customer_pref_summary_profile.json）。"
        ),
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)
