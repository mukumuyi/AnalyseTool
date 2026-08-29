"""customer_pref_summary: 顧客マスタ(customers)を地方区分(pref)ごとに集計し、
顧客区分(segment)で色分けした棒グラフ＋クリックで明細が見えるインタラクティブ
レポートを作るツール。

`scripts/customer_pref_summary.py` から呼ばれるエントリポイント。
前準備(EDA) → データ加工 → 分析 → 可視化 の4ステップを順に呼ぶ。
"""

from __future__ import annotations

from . import analyze, process, visualize
from .cli import parse_args
from .io import read_customers, write_profile, write_report_html
from .prepare import profile_customers


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    # ① 前準備（EDA）: 生データの傾向を把握する
    profile = profile_customers(args.input)
    write_profile(profile, args.profile_output)

    # ② データ加工: 欠損・重複を除いてクレンジング
    raw = read_customers(args.input)
    cleaned = process.clean_customers(raw)

    # ③ 分析: pref×segmentで集計し、明細データを抽出
    agg_df, pref_order, detail_df = analyze.aggregate_by_pref_segment(cleaned)

    # ④ 可視化: 棒グラフ＋クリックで明細を表示するレポートHTML
    html = visualize.build_report(agg_df, pref_order, detail_df)
    write_report_html(html, args.output)

    print(
        f"レポート出力完了: {args.output}"
        f"（顧客数={len(detail_df):,}件、地方区分数={len(pref_order)}）"
    )
