"""④ 可視化 — レポート全体の調整・グラフ配置・部品へのパラメータ受け渡し。

集計（`analyze.py`の責務）・描画（`common/charts/*`・`fast_client.py`の
責務）は持ち込まず、「どのグラフをどの段に、どんなパラメータで置くか」を
決めるだけの薄い調整役に徹する（`docs/development-guidelines.md`の
`visualize.py`肥大化対策）。⑥-2〜⑥-4は`common/report.py`を経由せず、
このモジュールが直接シェルHTMLを組み立てる（非同期`fetch()`を挟む構成が
既存の多段ドリルダウン機構の前提と合わないため。詳細は
`.steering/20260901-eqp-workload-fastview/design.md`の「課題対応」）。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from analyse_tool.common.charts.bar import stacked_bar
from analyse_tool.common.charts.barline import bar_with_line
from analyse_tool.common.charts.pareto import pareto_chart, pareto_data
from analyse_tool.common.charts.scatter import scatter
from analyse_tool.trial_factory.eqp_workload_fastview.fast_client import (
    build_fast_client_js,
)

REPORT_TITLE = "設備稼働負荷・ロット待機分析（高速モード対応版）"
BUSY_STATUS = "着工中"
WAIT_STATUS = "待機"
COLOR_BUSY = "#1f77b4"
# ⑥-3ガントの非稼働区間バー、および⑥-3仕掛数量推移の「待機中」帯で共用する
# （待機中は当初「自装置着工待ち」「他装置着工待ち」の2区分だったが、
# ユーザー指示により1区分へ統合した。design.md「追加設計5」参照）。
COLOR_WAIT = "#d3d3d3"
# ⑥-3ガントの装置ステータス背景（稼働中／待機中）。区間バー（COLOR_BUSY）
# より淡い色にして、バーの視認性を損なわないようにする。
COLOR_STATUS_PROCESSING = "#dceefb"
COLOR_STATUS_WAITING = "#eef0f2"

DISCLAIMER = (
    "サンプルデータ（generate_proc_history）は設備の同時使用制約（1台1ロット）を"
    "持たないため、ガントチャートのサブレーン数は実際の工場のバッチ挙動より"
    "多く出ます。"
)
SINGLE_FILE_NOTICE = (
    "この出力はサーバー不要の単一HTML版です。⑥-3・⑥-4は初期表示日のみ閲覧でき、"
    "他の日への切替には高速モード（--serve）を使ってください。"
)

LOT_DETAIL_COLUMNS = [
    "lot_id",
    "prodspec_id",
    "mainpd_id",
    "ope_no",
    "ope_seq",
    "eqp_id",
    "start_time",
    "end_time",
]


def build_daily_index_payload(daily_index_df: pd.DataFrame) -> dict[str, object]:
    """⑥-2用の日次インデックスをJSON化しやすいcolumnar形式にする。"""
    days = [str(d) for d in daily_index_df["day"]]
    return {
        "days": days,
        "utilization_pct": [
            round(float(v), 2) for v in daily_index_df["utilization_pct"]
        ],
        "start_count": [int(v) for v in daily_index_df["start_count"]],
    }


def build_day_payload(
    date_str: str,
    laned_segments_df: pd.DataFrame,
    wip_df: pd.DataFrame,
    lot_detail_df: pd.DataFrame,
    eqp_ids: list[str],
    day_start: pd.Timestamp,
) -> dict[str, object]:
    """⑥-3/⑥-4用の1日分ペイロード（`data/days/<日付>.json`の中身）を組み立てる。

    Args:
        date_str: 対象日（`YYYY-MM-DD`）。
        laned_segments_df: `analyze.assign_lanes_to_segments()`の結果
            （当日境界にクリップ済み・`lane`列付き）。
        wip_df: `analyze.build_day_wip_series()`の結果。
        lot_detail_df: `analyze.build_lot_records()`の結果（当日分）。
        eqp_ids: 対象設備群（パレート上位N台。表示順を保持する）。
        day_start: 当日0時（`start_min`/`end_min`の起点）。

    Returns:
        `fast_client.py`のJSがそのまま読める構造の辞書。
    """
    if laned_segments_df.empty:
        segments: dict[str, list[object]] = {
            "eqp_id": [],
            "lane": [],
            "start_min": [],
            "end_min": [],
            "lot_id": [],
        }
    else:
        start_min = (
            laned_segments_df["start_time"] - day_start
        ).dt.total_seconds() / 60
        end_min = (laned_segments_df["end_time"] - day_start).dt.total_seconds() / 60
        segments = {
            "eqp_id": laned_segments_df["eqp_id"].tolist(),
            "lane": [int(v) for v in laned_segments_df["lane"]],
            "start_min": [round(float(v), 3) for v in start_min],
            "end_min": [round(float(v), 3) for v in end_min],
            "lot_id": laned_segments_df["lot_id"].tolist(),
        }

    if wip_df.empty:
        wip: dict[str, list[object]] = {
            "t_min": [],
            "busy": [],
            "wait": [],
        }
    else:
        t_min = (wip_df["t"] - day_start).dt.total_seconds() / 60
        wip = {
            "t_min": [round(float(v), 1) for v in t_min],
            "busy": [int(v) for v in wip_df["busy"]],
            "wait": [int(v) for v in wip_df["wait"]],
        }

    lot_detail_data: dict[str, list[object]] = {}
    for col in LOT_DETAIL_COLUMNS:
        if col in ("start_time", "end_time") and not lot_detail_df.empty:
            lot_detail_data[col] = (
                lot_detail_df[col].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist()
            )
        else:
            lot_detail_data[col] = (
                lot_detail_df[col].tolist() if not lot_detail_df.empty else []
            )

    return {
        "date": date_str,
        "eqp_ids": list(eqp_ids),
        "segments": segments,
        "wip": wip,
        "lot_detail": {"columns": LOT_DETAIL_COLUMNS, "data": lot_detail_data},
    }


def build_report(
    workload_df: pd.DataFrame,
    pareto_df: pd.DataFrame,
    daily_index_df: pd.DataFrame,
    initial_date: str,
    initial_day_payload: dict[str, object],
    *,
    top_n: int,
    row_count: int,
    eqp_count: int,
    single_file: bool,
) -> str:
    """①〜⑤・⑥-1〜⑥-4を1枚のシェルHTML文字列に組み立てる。"""
    lead_sections_html = "\n".join(
        [
            _build_section1_proc_count(workload_df),
            _build_section2_wait_total(workload_df),
            _build_section3_wait_avg(workload_df),
            _build_section4_scatter_total(workload_df, top_n),
            _build_section5_scatter_avg(workload_df, top_n),
        ]
    )
    pareto_html = _build_stage1_pareto_html(pareto_df)
    daily_fig_html = _build_daily_fig_html(daily_index_df)

    fast_client_js = build_fast_client_js(
        data_base_url="data/days/",
        initial_date=initial_date,
        initial_day_payload=initial_day_payload,
        single_file=single_file,
        color_busy=COLOR_BUSY,
        color_wait=COLOR_WAIT,
        color_status_processing=COLOR_STATUS_PROCESSING,
        color_status_waiting=COLOR_STATUS_WAITING,
    )

    disclaimer = (
        f"{DISCLAIMER}（全{row_count:,}行 / 設備{eqp_count}台 / 上位{top_n}台を対象）"
    )
    if single_file:
        disclaimer = f"{disclaimer}<br>{SINGLE_FILE_NOTICE}"

    return _SHELL_TEMPLATE.format(
        title=_escape(REPORT_TITLE),
        disclaimer_html=disclaimer,
        lead_sections_html=lead_sections_html,
        top_n=top_n,
        pareto_html=pareto_html,
        daily_fig_html=daily_fig_html,
        color_status_processing=COLOR_STATUS_PROCESSING,
        color_status_waiting=COLOR_STATUS_WAITING,
        lot_detail_header_html="".join(
            f"<th>{_escape(c)}</th>" for c in LOT_DETAIL_COLUMNS
        ),
        fast_client_js=fast_client_js,
    )


def _fig_section(heading: str, fig: go.Figure, div_id: str) -> str:
    fig_html = fig.to_html(full_html=False, include_plotlyjs=False, div_id=div_id)
    return f"<section><h3>{heading}</h3>{fig_html}</section>"


def _build_section1_proc_count(workload_df: pd.DataFrame, top_n: int = 15) -> str:
    top_df = pareto_data(
        workload_df, category="eqp_id", value="proc_count", top_n=top_n
    )
    fig = stacked_bar(
        top_df,
        x="eqp_id",
        y="proc_count",
        x_order=list(top_df["eqp_id"]),
        title=f"①設備ごとの処理数（上位{top_n}台）",
        x_title="設備",
        y_title="処理数",
    )
    return _fig_section("①設備ごとの処理数", fig, "section1-chart")


def _build_section2_wait_total(workload_df: pd.DataFrame, top_n: int = 10) -> str:
    top_df = pareto_data(
        workload_df, category="eqp_id", value="wait_total_minutes", top_n=top_n
    )
    fig = stacked_bar(
        top_df,
        x="eqp_id",
        y="wait_total_minutes",
        x_order=list(top_df["eqp_id"]),
        title=f"②設備ごとのロット待機時間（合計、上位{top_n}台）",
        x_title="設備",
        y_title="待機時間合計（分）",
    )
    return _fig_section("②設備ごとのロット待機時間（合計）", fig, "section2-chart")


def _build_section3_wait_avg(workload_df: pd.DataFrame, top_n: int = 10) -> str:
    top_df = pareto_data(
        workload_df, category="eqp_id", value="wait_avg_minutes", top_n=top_n
    )
    fig = stacked_bar(
        top_df,
        x="eqp_id",
        y="wait_avg_minutes",
        x_order=list(top_df["eqp_id"]),
        title=f"③設備ごとのロット待機時間（平均、上位{top_n}台）",
        x_title="設備",
        y_title="待機時間平均（分）",
    )
    return _fig_section("③設備ごとのロット待機時間（平均）", fig, "section3-chart")


def _build_section4_scatter_total(workload_df: pd.DataFrame, top_n: int) -> str:
    top_df = pareto_data(
        workload_df, category="eqp_id", value="wait_total_minutes", top_n=top_n
    )
    fig = scatter(
        top_df,
        x="proc_count",
        y="wait_total_minutes",
        text="eqp_id",
        title=f"④処理数×待機時間（合計）の関係（上位{top_n}台）",
        x_title="処理数",
        y_title="待機時間合計（分）",
    )
    return _fig_section("④処理数×待機時間（合計）の関係", fig, "section4-chart")


def _build_section5_scatter_avg(workload_df: pd.DataFrame, top_n: int) -> str:
    top_df = pareto_data(
        workload_df, category="eqp_id", value="wait_total_minutes", top_n=top_n
    )
    fig = scatter(
        top_df,
        x="proc_count",
        y="wait_avg_minutes",
        text="eqp_id",
        title=f"⑤処理数×待機時間（平均）の関係（上位{top_n}台）",
        x_title="処理数",
        y_title="待機時間平均（分）",
    )
    return _fig_section("⑤処理数×待機時間（平均）の関係", fig, "section5-chart")


def _build_stage1_pareto_html(pareto_df: pd.DataFrame) -> str:
    fig = pareto_chart(
        pareto_df,
        category="eqp_id",
        value="wait_total_minutes",
        title="設備別 待機時間合計（パレート図）",
        x_title="設備",
        y_title="待機時間合計（分）",
    )
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id="stage1-pareto")


def _build_daily_fig_html(daily_index_df: pd.DataFrame) -> str:
    df = daily_index_df.copy()
    df["day"] = df["day"].astype(str)
    fig = bar_with_line(
        df,
        x="day",
        y_bar="utilization_pct",
        y_line="start_count",
        x_order=list(df["day"]),
        title="日別稼働率・処理数",
        x_title="日",
        y_bar_title="稼働率（%）",
        y_line_title="着工件数",
        line_name="着工件数",
    )
    return fig.to_html(
        full_html=False, include_plotlyjs=False, div_id="stage2-daily-chart"
    )


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


_SHELL_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="https://cdn.plot.ly/plotly-3.0.1.min.js"></script>
<style>
  body {{ font-family: -apple-system, "Hiragino Sans", "Yu Gothic", sans-serif; margin: 24px; }}
  h1 {{ font-size: 1.4em; }}
  h2 {{ font-size: 1.15em; margin-top: 32px; border-top: 1px solid #ddd; padding-top: 16px; }}
  h3 {{ font-size: 1em; }}
  section {{ margin-bottom: 8px; }}
  #disclaimer {{ background: #fff8e1; border: 1px solid #ffe082; padding: 8px 12px;
                 font-size: 0.85em; color: #6b5600; margin-bottom: 16px; }}
  .hint {{ color: #666; font-size: 0.85em; margin: 4px 0; }}
  details.lead-details {{ border: 1px solid #ddd; border-radius: 6px; padding: 4px 12px; margin-bottom: 10px; }}
  details.lead-details > summary {{ cursor: pointer; font-weight: bold; padding: 8px 0; }}

  .gantt-head-row {{ display: grid; grid-template-columns: 140px 1fr; }}
  .gantt-axis {{ position: relative; height: 18px; font-size: 11px; color: #888; }}
  .gantt-axis span {{ position: absolute; transform: translateX(-50%); }}
  .gantt-body-row {{ display: grid; grid-template-columns: 140px 1fr; align-items: start; }}
  .gantt-labels {{ display: flex; flex-direction: column; }}
  .gantt-label-row {{ display: flex; align-items: center; font-size: 8px; font-weight: bold;
                       overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }}
  .gantt-canvas {{ width: 100%; display: block; cursor: grab; touch-action: none; }}
  .wip-wrap {{ margin-top: 14px; padding-top: 10px; border-top: 1px solid #eee; }}
  .wip-title {{ font-size: 0.85em; color: #666; margin-bottom: 4px; }}
  .wip-body-row {{ display: grid; grid-template-columns: 140px 1fr; }}
  .wip-axis {{ position: relative; height: 90px; font-size: 9px; color: #888; }}
  .wip-axis span {{ position: absolute; right: 6px; transform: translateY(-50%); }}
  .wip-canvas {{ width: 100%; height: 90px; display: block; }}
  .legend-row {{ display: flex; gap: 16px; font-size: 11.5px; color: #666; margin-top: 6px; }}
  .legend-row .sw {{ display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 5px; }}

  table {{ border-collapse: collapse; font-size: 0.9em; }}
  th, td {{ border: 1px solid #ddd; padding: 4px 10px; text-align: left; }}
  th {{ background: #f4f4f4; position: sticky; top: 0; }}
  #stage4-table-wrap {{ max-height: 480px; overflow: auto; border: 1px solid #eee; }}

  .gantt-tooltip {{
    position: fixed; pointer-events: none; z-index: 50; background: #222; color: #fff;
    font-size: 11px; padding: 4px 7px; border-radius: 4px; opacity: 0; transition: opacity .08s;
    transform: translate(-50%, -100%);
  }}
</style>
</head>
<body>
<h1>{title}</h1>
<div id="disclaimer">{disclaimer_html}</div>

<details class="lead-details">
  <summary>①〜⑤ 概要指標（設備ごとの処理数・待機時間・散布図）</summary>
  {lead_sections_html}
</details>

<details class="lead-details" open>
  <summary>⑥-1 パレート図（設備別 待機時間合計、上位{top_n}台）</summary>
  {pareto_html}
</details>

<h2>⑥-2 日別稼働率・処理数（直近1ヶ月・日次）</h2>
<div class="hint">日の棒をクリックすると、その日の⑥-3ガントが下に表示されます。</div>
{daily_fig_html}

<h2>⑥-3 <span id="stage3-heading-date"></span> 設備別ガント＋全仕掛数量推移</h2>
<div class="hint">着工中区間（青）をクリックすると、そのロットの⑥-4明細が下に表示されます。ロット名はガント上には表示しません。マウスホイールでズーム、ドラッグで横方向にパン、ダブルクリックで全期間表示に戻せます（下の仕掛数量推移も同じ表示範囲に連動します）。</div>
<div class="legend-row">
  <span><i class="sw" style="background:{color_status_processing};border:1px solid #b6d9f3;"></i>装置ステータス: 稼働中(Processing)</span>
  <span><i class="sw" style="background:{color_status_waiting};border:1px solid #ccc;"></i>装置ステータス: 待機中(Waiting)</span>
</div>
<div class="gantt-head-row">
  <div></div>
  <div id="gantt-axis" class="gantt-axis"></div>
</div>
<div class="gantt-body-row">
  <div id="gantt-labels" class="gantt-labels"></div>
  <canvas id="gantt-canvas" class="gantt-canvas"></canvas>
</div>
<div class="wip-wrap">
  <div class="wip-title">全仕掛数量推移（着工中／待機中。⑥-3ガントと表示範囲が連動します）</div>
  <div class="wip-body-row">
    <div id="wip-axis" class="wip-axis"></div>
    <canvas id="wip-canvas" class="wip-canvas"></canvas>
  </div>
  <div class="legend-row">
    <span><i class="sw" style="background:#1f77b4;"></i>着工中</span>
    <span><i class="sw" style="background:#d3d3d3;"></i>待機中</span>
  </div>
</div>

<h2>⑥-4 選択ロットのグループ内工程明細</h2>
<div id="stage4-hint" class="hint">まだロットが選択されていません。</div>
<div id="stage4-table-wrap">
  <table>
    <thead><tr>{lot_detail_header_html}</tr></thead>
    <tbody id="stage4-body"></tbody>
  </table>
</div>

<div id="gantt-tooltip" class="gantt-tooltip"></div>

<script>
{fast_client_js}
</script>
<script>
(function () {{
  var dailyChart = document.getElementById("stage2-daily-chart");
  dailyChart.on("plotly_click", function (eventData) {{
    var day = String(eventData.points[0].x);
    window.FastView.selectDay(day);
  }});
}})();
</script>
</body>
</html>
"""
