"""eqp_workload_fastview の引数定義。"""

from __future__ import annotations

import argparse

from analyse_tool.trial_factory.eqp_workload_fastview.analyze import DEFAULT_TOP_N

DEFAULT_PERIOD_DAYS = 0  # 0 = 入力データの全期間を対象にする


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eqp_workload_fastview",
        description=(
            "proc_historyから設備ごとの稼働負荷・ロット待機時間を集計し、"
            "①〜⑤・パレート図（⑥-1）に加え、⑥-2で全期間の日次稼働率・"
            "処理数を、⑥-3で選択日1日分の複数設備ガント＋仕掛数量推移を、"
            "⑥-4で選択ロットの明細を表示するレポートを作る。"
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
        "trial_factory/<実行日>/にレポートディレクトリ・プロファイルを書き出す。",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=DEFAULT_TOP_N,
        help=f"パレート図・⑥-2〜⑥-4の対象にする上位設備数（既定: {DEFAULT_TOP_N}）。",
    )
    parser.add_argument(
        "--period-days",
        type=int,
        default=DEFAULT_PERIOD_DAYS,
        help="⑥-2の対象期間（日数、入力データの最初の日から）。"
        "既定の0は入力データの全期間を対象にする。",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="レポート生成後、ローカル静的サーバーで即座に配信する（高速モード）。",
    )
    parser.add_argument(
        "--single-file",
        action="store_true",
        help="日別データを別ファイルへ分割せず、初期表示日のみ埋め込んだ"
        "単一HTMLを出力する（サーバー起動不要。⑥-3/⑥-4は他日へ切替不可）。",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)
