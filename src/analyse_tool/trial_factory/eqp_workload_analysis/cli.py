"""eqp_workload_analysis の引数定義。"""

from __future__ import annotations

import argparse

from analyse_tool.trial_factory.eqp_workload_analysis.analyze import (
    DEFAULT_PERIOD_DAYS,
    DEFAULT_TOP_N,
)

DEFAULT_GANTT_WINDOW_HOURS = 4


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eqp_workload_analysis",
        description=(
            "proc_historyから設備ごとの稼働負荷・ロット待機時間を集計し、"
            "パレート図→装置稼働グラフ→ガントチャート＋仕掛数量推移→"
            "ロット明細表の4段階ドリルダウン付きレポートを作る。"
        ),
    )
    parser.add_argument(
        "--input",
        default="data/trial_factory/proc_history.parquet",
        help="proc_historyのParquetファイルパス（既定: data/trial_factory/proc_history.parquet）。",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="出力ルートディレクトリ（既定: output）。この配下の"
        "trial_factory/<実行日>/にレポート・プロファイルを書き出す。",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=DEFAULT_TOP_N,
        help=f"パレート図・ドリルダウンの対象にする上位設備数（既定: {DEFAULT_TOP_N}）。",
    )
    parser.add_argument(
        "--period-days",
        type=int,
        default=DEFAULT_PERIOD_DAYS,
        help=f"装置稼働グラフの代表期間（日数、既定: {DEFAULT_PERIOD_DAYS}）。",
    )
    parser.add_argument(
        "--gantt-window-hours",
        type=int,
        default=DEFAULT_GANTT_WINDOW_HOURS,
        help=f"ガントチャートの初期表示窓幅（時間、既定: {DEFAULT_GANTT_WINDOW_HOURS}）。",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)
