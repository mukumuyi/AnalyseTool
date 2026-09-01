"""eqp_workload_fastview: proc_historyを対象に、設備ごとの稼働負荷・ロット
待機時間を集計し、①〜⑤・⑥-1（パレート図）に加え、⑥-2で全期間の日次
稼働率・処理数、⑥-3で選択日1日分の複数設備ガント＋全仕掛数量推移、⑥-4で
選択ロットの明細を表示するレポートを作るツール。

`eqp_workload_analysis`（旧版）の⑥-2（代表期間3日・1時間刻み）・⑥-3
（4時間窓・単一設備）を、⑥-2は1ヶ月・日次、⑥-3は1日・複数設備＋
サブレーンへ拡張したもの。旧版ツールは変更していない別ツール
（`.steering/20260901-eqp-workload-fastview/`参照）。

`scripts/trial_factory/eqp_workload_fastview.py`から呼ばれるエントリ
ポイント。前準備(EDA) → データ加工 → 分析 → 可視化 の4ステップを
順に呼ぶ。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd

from analyse_tool.trial_factory.eqp_workload_fastview import (
    analyze,
    process,
    server,
    visualize,
)
from analyse_tool.trial_factory.eqp_workload_fastview.cli import parse_args
from analyse_tool.trial_factory.eqp_workload_fastview.io import (
    read_proc_history,
    write_fastview_report,
    write_profile,
)
from analyse_tool.trial_factory.eqp_workload_fastview.prepare import (
    profile_proc_history,
)

PROJECT_NAME = "trial_factory"
TOOL_NAME = "eqp_workload_fastview"


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
    report_dir = run_dir / f"{TOOL_NAME}_{time_suffix}"
    write_profile(profile, str(profile_output_path))

    # ② データ加工: 欠損・型を整形し、待機時間・前後工程の設備IDを付与
    con, raw = read_proc_history(args.input)
    cleaned = process.clean_proc_history(raw)
    annotated_lazy = process.annotate_lot_sequence(cleaned)
    # ⑥-3/⑥-4は日ごとに何度も問い合わせるため、遅延評価のまま渡さず
    # 実テーブル化する（`process.materialize()`のdocstring参照）。
    annotated = process.materialize(con, annotated_lazy)

    # ③ 分析: ①〜⑤・⑥-1の負荷集計・パレート
    workload_df = analyze.aggregate_eqp_workload(annotated)
    pareto_df = analyze.build_pareto(workload_df, top_n=args.top_n)
    top_eqp_ids = list(pareto_df["eqp_id"])

    row_count, eqp_count = _fetchone(
        annotated.aggregate("COUNT(*), COUNT(DISTINCT eqp_id)")
    )

    # ⑥-2: 全期間（または--period-days指定分）の日次インデックス
    daily_index_df = analyze.aggregate_daily_index(annotated, top_eqp_ids)
    if daily_index_df.empty:
        raise RuntimeError("対象設備群のデータが見つかりませんでした")
    if args.period_days > 0:
        daily_index_df = daily_index_df.head(args.period_days).reset_index(drop=True)

    # ⑥-3/⑥-4: 稼働が最も多い日を初期表示にする（空の初期画面を避ける）
    initial_day = daily_index_df.loc[daily_index_df["busy_minutes"].idxmax(), "day"]
    initial_date_str = str(initial_day)

    target_dates = (
        [initial_date_str]
        if args.single_file
        else [str(d) for d in daily_index_df["day"]]
    )
    day_payloads = {
        date_str: _build_one_day_payload(annotated, top_eqp_ids, date_str)
        for date_str in target_dates
    }
    initial_payload = day_payloads[initial_date_str]

    # ④ 可視化: シェルHTML＋日次インデックス＋日別ペイロード
    html = visualize.build_report(
        workload_df,
        pareto_df,
        daily_index_df,
        initial_date_str,
        initial_payload,
        top_n=args.top_n,
        row_count=row_count,
        eqp_count=eqp_count,
        single_file=args.single_file,
    )
    daily_index_payload = visualize.build_daily_index_payload(daily_index_df)

    index_path = write_fastview_report(
        output_dir=str(report_dir),
        shell_html=html,
        daily_index_payload=daily_index_payload,
        day_payloads={} if args.single_file else day_payloads,
        project_output_dir=str(project_output_dir),
        note=(
            f"{row_count:,}行 / 設備{eqp_count}台 / 上位{args.top_n}台 / "
            f"{len(daily_index_df)}日分"
            + ("（単一HTML）" if args.single_file else "（高速モード対応）")
        ),
    )

    print(
        f"レポート出力完了: {index_path}"
        f"（{row_count:,}行、設備{eqp_count}台、上位{args.top_n}台、"
        f"{len(daily_index_df)}日分、初期表示日 {initial_date_str}）"
    )

    if args.serve:
        server.serve(str(report_dir))


def _build_one_day_payload(
    annotated: duckdb.DuckDBPyRelation,
    top_eqp_ids: list[str],
    date_str: str,
) -> dict[str, object]:
    day_start = pd.Timestamp(date_str)
    day_end = day_start + pd.Timedelta(days=1)
    segments_df = analyze.build_day_segments(annotated, top_eqp_ids, day_start, day_end)
    laned_df = analyze.assign_lanes_to_segments(segments_df)
    wip_df = analyze.build_day_wip_series(annotated, top_eqp_ids, day_start, day_end)
    lot_detail_df = analyze.build_lot_records(
        annotated, top_eqp_ids, day_start, day_end
    )
    return visualize.build_day_payload(
        date_str, laned_df, wip_df, lot_detail_df, top_eqp_ids, day_start
    )
