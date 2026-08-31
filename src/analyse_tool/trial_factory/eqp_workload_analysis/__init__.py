"""eqp_workload_analysis: proc_historyを対象に、設備ごとの稼働負荷・
ロット待機時間を集計し、パレート図→装置稼働グラフ→ガントチャート＋
仕掛数量推移→ロット明細表の4段階ドリルダウン付きレポートを作るツール。

`scripts/trial_factory/eqp_workload_analysis.py`から呼ばれるエントリ
ポイント。前準備(EDA) → データ加工 → 分析 → 可視化 の4ステップを
順に呼ぶ。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd

from analyse_tool.trial_factory.eqp_workload_analysis import analyze, process, visualize
from analyse_tool.trial_factory.eqp_workload_analysis.cli import parse_args
from analyse_tool.trial_factory.eqp_workload_analysis.io import (
    read_proc_history,
    write_profile,
    write_report_html,
)
from analyse_tool.trial_factory.eqp_workload_analysis.prepare import (
    profile_proc_history,
)

PROJECT_NAME = "trial_factory"
TOOL_NAME = "eqp_workload_analysis"


def _fetchone(result: duckdb.DuckDBPyRelation) -> tuple:
    """`fetchone()`の結果を返す（`None`はここで異常として扱う）。"""
    row = result.fetchone()
    if row is None:
        raise RuntimeError("集計クエリの結果が空でした")
    return row


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    run_at = datetime.now()

    # ① 前準備（EDA）: 生データの傾向を把握する
    profile = profile_proc_history(args.input)

    project_output_dir = Path(args.output_dir) / PROJECT_NAME
    run_dir = project_output_dir / run_at.strftime("%Y%m%d")
    time_suffix = run_at.strftime("%H%M%S")
    profile_output_path = run_dir / f"{TOOL_NAME}_profile_{time_suffix}.json"
    report_output_path = run_dir / f"{TOOL_NAME}_{time_suffix}.html"
    write_profile(profile, str(profile_output_path))

    # ② データ加工: 欠損・型を整形し、待機時間・前後工程の設備IDを付与
    raw = read_proc_history(args.input)
    cleaned = process.clean_proc_history(raw)
    annotated = process.annotate_lot_sequence(cleaned)

    # ③ 分析: 設備ごとの負荷集計、パレート、代表期間の時間帯別集計・明細抽出
    workload_df = analyze.aggregate_eqp_workload(annotated)
    pareto_df = analyze.build_pareto(workload_df, top_n=args.top_n)
    top_eqp_ids = list(pareto_df["eqp_id"])

    period_start = pd.Timestamp(_fetchone(annotated.aggregate("MIN(start_time)"))[0])
    period_end = period_start + pd.Timedelta(days=args.period_days)

    hourly_df = analyze.build_hourly_utilization(
        annotated, top_eqp_ids, period_start, period_end
    )
    lot_df = analyze.build_lot_records(annotated, top_eqp_ids, period_start, period_end)

    row_count, eqp_count = _fetchone(
        annotated.aggregate("COUNT(*), COUNT(DISTINCT eqp_id)")
    )

    # ④ 可視化: 4段階ドリルダウン付きレポートHTML
    html = visualize.build_report(
        workload_df,
        pareto_df,
        hourly_df,
        lot_df,
        top_n=args.top_n,
        gantt_window_hours=args.gantt_window_hours,
        row_count=row_count,
        eqp_count=eqp_count,
    )
    write_report_html(
        html,
        str(report_output_path),
        project_output_dir=str(project_output_dir),
        note=f"{row_count:,}行 / 設備{eqp_count}台 / 上位{args.top_n}台",
    )

    print(
        f"レポート出力完了: {report_output_path}"
        f"（{row_count:,}行、設備{eqp_count}台、上位{args.top_n}台、"
        f"代表期間 {period_start:%Y-%m-%d} 〜 {period_end:%Y-%m-%d}）"
    )
