"""④ 可視化 — レポート全体の調整・グラフ配置・部品へのパラメータ受け渡し。

集計（`analyze.py`の責務）・描画（`common/charts/*`の責務）は持ち込まず、
「どのグラフをどの段に、どんなパラメータで置くか」を決めるだけの薄い
調整役に徹する（`docs/development-guidelines.md`の`visualize.py`肥大化
対策）。レポートのセクションごとに小さいプライベート関数へ分割する。

段2→段3（装置稼働グラフ→ガントチャート＋仕掛数量推移）・段3→段4
（ガントチャート→ロット明細表）は「構築式」（`common/report.py`参照）の
ため、ガントチャートの並行処理枠への詰め直し（貪欲法）・仕掛数量の
3分類集計は、Pythonで重複実装せずブラウザ側のJS（`_build_domain_js()`）
だけに実装する。ページを開いた直後の初期表示も、同じJSが1回自動実行
されることで作る（Python側に別実装を持たない）。
"""

from __future__ import annotations

from typing import cast

import pandas as pd
import plotly.graph_objects as go

from analyse_tool.common.charts.bar import stacked_bar
from analyse_tool.common.charts.barline import bar_with_line
from analyse_tool.common.charts.pareto import pareto_chart, pareto_data
from analyse_tool.common.charts.scatter import scatter
from analyse_tool.common.charts.twograph import GANTT_CURVE_NUMBER, gantt_and_wip_chart
from analyse_tool.common.report import build_multi_stage_drilldown_html

REPORT_TITLE = "設備稼働負荷・ロット待機分析"
BUSY_STATUS = "着工中"
WAIT_STATUS = "待機"
COLOR_BUSY = "#1f77b4"
COLOR_WAIT = "#d3d3d3"
COLOR_WAIT_SELF = "#ff7f0e"
COLOR_WAIT_OTHER = "#2ca02c"

DISCLAIMER = (
    "サンプルデータ（generate_proc_history）は設備の同時使用制約（1台1ロット）を"
    "持たないため、ガントチャートの並行処理枠数は実際の工場のバッチ挙動より"
    "多く出ます。"
)


def build_report(
    workload_df: pd.DataFrame,
    pareto_df: pd.DataFrame,
    hourly_df: pd.DataFrame,
    lot_df: pd.DataFrame,
    *,
    top_n: int,
    gantt_window_hours: int,
    row_count: int,
    eqp_count: int,
) -> str:
    """4つの集計データフレームからレポートHTML文字列を組み立てる。"""
    lead_sections_html = [
        _build_section1_proc_count(workload_df),
        _build_section2_wait_total(workload_df),
        _build_section3_wait_avg(workload_df),
        _build_section4_scatter_total(workload_df, top_n),
        _build_section5_scatter_avg(workload_df, top_n),
    ]

    stage1_fig = _build_stage1_pareto(pareto_df)
    top_eqp_ids = list(pareto_df["eqp_id"])

    stage2_figs = _build_stage2_figs(hourly_df, top_eqp_ids)
    default_eqp_id = top_eqp_ids[0]
    default_hour = _default_hour(hourly_df, default_eqp_id)

    stage3_default_fig = _build_stage3_placeholder()

    lot_detail_columns, lot_detail_data = _lot_detail_to_columnar(lot_df)
    domain_js = _build_domain_js(
        default_eqp_id=default_eqp_id,
        default_hour_iso=default_hour.isoformat(),
        gantt_window_hours=gantt_window_hours,
    )

    return build_multi_stage_drilldown_html(
        title=REPORT_TITLE,
        lead_sections_html=lead_sections_html,
        stage1_fig=stage1_fig,
        stage1_heading=f"⑥-1 パレート図（設備別 待機時間合計、上位{top_n}台）",
        stage2_figs=stage2_figs,
        stage2_default_key=default_eqp_id,
        stage2_heading="⑥-2 装置稼働グラフ",
        stage3_default_fig=stage3_default_fig,
        stage3_heading="⑥-3 ガントチャート＋仕掛数量推移",
        stage3_curve_number=GANTT_CURVE_NUMBER,
        stage4_heading="⑥-4 ロット明細表",
        lot_detail_columns=lot_detail_columns,
        lot_detail_data=lot_detail_data,
        domain_js=domain_js,
        disclaimer=(
            f"{DISCLAIMER} （全{row_count:,}行 / 設備{eqp_count}台 / 上位{top_n}台を対象）"
        ),
    )


def _fig_section(heading: str, fig: go.Figure, div_id: str) -> str:
    fig_html = fig.to_html(full_html=False, include_plotlyjs=False, div_id=div_id)
    return f"<section><h2>{heading}</h2>{fig_html}</section>"


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


def _build_stage1_pareto(pareto_df: pd.DataFrame) -> go.Figure:
    return pareto_chart(
        pareto_df,
        category="eqp_id",
        value="wait_total_minutes",
        title="設備別 待機時間合計（パレート図）",
        x_title="設備",
        y_title="待機時間合計（分）",
    )


def _build_stage2_figs(
    hourly_df: pd.DataFrame, eqp_ids: list[str]
) -> dict[str, go.Figure]:
    figs = {}
    for eqp_id in eqp_ids:
        sub = hourly_df[hourly_df["eqp_id"] == eqp_id]
        hour_order = sorted(sub["hour_start"].unique())
        figs[eqp_id] = bar_with_line(
            sub,
            x="hour_start",
            y_bar="minutes",
            y_line="start_count",
            color="status",
            x_order=[pd.Timestamp(h) for h in hour_order],
            title=f"{eqp_id} 装置稼働グラフ",
            x_title="時刻",
            y_bar_title="分（1時間あたり）",
            y_line_title="着工件数",
            line_name="着工件数",
        )
    return figs


def _default_hour(hourly_df: pd.DataFrame, eqp_id: str) -> pd.Timestamp:
    """初期表示するガントチャートの中心時刻を選ぶ。

    代表期間には稼働がほぼ無い時間帯も多いため、単純に期間の先頭を選ぶと
    何も表示されない初期画面になりやすい。最も稼働（着工中の分数）が
    多い時間帯を選び、意味のある初期表示にする。
    """
    sub = hourly_df[
        (hourly_df["eqp_id"] == eqp_id) & (hourly_df["status"] == BUSY_STATUS)
    ]
    if sub.empty or sub["minutes"].max() == 0:
        return pd.Timestamp(
            hourly_df[hourly_df["eqp_id"] == eqp_id]["hour_start"].min()
        )
    busiest_hour = sub.loc[sub["minutes"].idxmax()]
    # pandas-stubsではSeriesの要素アクセスの戻り値型が広すぎて
    # `pd.Timestamp()`の引数と噛み合わないため、実際の値の型を明示する。
    return pd.Timestamp(cast(str, busiest_hour.at["hour_start"]))


def _build_stage3_placeholder() -> go.Figure:
    """段3の初期の入れ物となる空のFigureを作る（実際の中身はJSが描く）。

    ページを開いた直後にドメインJSが1回自動実行され、この空Figureを
    `Plotly.react()`で実データに置き換える。トレース構成（ガント1本＋
    仕掛数量推移3本）はJS側と揃えてあるので、`GANTT_CURVE_NUMBER`は
    最初から正しい。
    """
    empty_gantt = pd.DataFrame(
        {
            "lane": pd.Series(dtype="int64"),
            "start": pd.Series(dtype="datetime64[ns]"),
            "end": pd.Series(dtype="datetime64[ns]"),
            "lot_id": pd.Series(dtype="object"),
            "status": pd.Series(dtype="object"),
        }
    )
    empty_wip = pd.DataFrame(
        {
            "t": pd.Series(dtype="datetime64[ns]"),
            "cat": pd.Series(dtype="object"),
            "n": pd.Series(dtype="int64"),
        }
    )
    return gantt_and_wip_chart(
        empty_gantt,
        empty_wip,
        gantt_start="start",
        gantt_end="end",
        gantt_lane="lane",
        gantt_label="lot_id",
        gantt_color="status",
        gantt_colors={BUSY_STATUS: COLOR_BUSY, WAIT_STATUS: COLOR_WAIT},
        wip_x="t",
        wip_y="n",
        wip_color="cat",
        wip_color_order=["busy", "wait_self", "wait_other"],
        wip_colors={
            "busy": COLOR_BUSY,
            "wait_self": COLOR_WAIT_SELF,
            "wait_other": COLOR_WAIT_OTHER,
        },
        gantt_y_title="並行処理枠",
        wip_y_title="仕掛数量",
    )


def _lot_detail_to_columnar(
    lot_df: pd.DataFrame,
) -> tuple[list[str], dict[str, list[object]]]:
    """`LotDetail`をJS側で`new Date(...)`が解釈できるISO8601文字列列にして
    columnar形式（`{列名: [値, ...]}`）に変換する。
    """
    columns = list(lot_df.columns)
    formatted = lot_df.copy()
    for col in ("start_time", "end_time"):
        formatted[col] = formatted[col].dt.strftime("%Y-%m-%dT%H:%M:%S.%f")
    data = {
        col: [None if pd.isna(v) else v for v in formatted[col].tolist()]
        for col in columns
    }
    return columns, data


def _build_domain_js(
    *, default_eqp_id: str, default_hour_iso: str, gantt_window_hours: int
) -> str:
    """段2→段3・段3→段4を「構築式」で組み立てるドメイン固有JSを作る。

    `window.EqpDrilldown`に`onStage1Select`/`onStage2Select`/
    `onStage3Select`を定義する（`common/report.py`が呼び出す契約）。
    ページを開いた直後、既定の設備・時間帯で段3を1回自動描画する。
    """
    return f"""
window.EqpDrilldown = (function () {{
  var COLOR_BUSY = {COLOR_BUSY!r};
  var COLOR_WAIT = {COLOR_WAIT!r};
  var COLOR_WAIT_SELF = {COLOR_WAIT_SELF!r};
  var COLOR_WAIT_OTHER = {COLOR_WAIT_OTHER!r};
  var GANTT_WINDOW_HOURS = {gantt_window_hours};
  var WIP_BUCKET_MINUTES = 15;

  function parseRows() {{
    var cols = window.LOT_DETAIL.columns;
    var data = window.LOT_DETAIL.data;
    var n = data[cols[0]] ? data[cols[0]].length : 0;
    var rows = [];
    for (var i = 0; i < n; i++) {{
      var row = {{}};
      for (var c = 0; c < cols.length; c++) {{
        row[cols[c]] = data[cols[c]][i];
      }}
      row.start_time = new Date(row.start_time);
      row.end_time = new Date(row.end_time);
      rows.push(row);
    }}
    return rows;
  }}

  var ALL_ROWS = parseRows();
  var BY_LOT_SEQ = {{}};
  ALL_ROWS.forEach(function (r) {{
    BY_LOT_SEQ[r.lot_id + "|" + r.ope_seq] = r;
  }});

  function rowsForEqp(eqpId) {{
    return ALL_ROWS.filter(function (r) {{ return r.eqp_id === eqpId; }});
  }}

  function greedyPackLanes(segments) {{
    segments.sort(function (a, b) {{ return a.start - b.start; }});
    var laneEnds = [];
    segments.forEach(function (seg) {{
      var laneIdx = -1;
      for (var i = 0; i < laneEnds.length; i++) {{
        if (laneEnds[i] <= seg.start) {{ laneIdx = i; break; }}
      }}
      if (laneIdx === -1) {{
        laneIdx = laneEnds.length;
        laneEnds.push(seg.end);
      }} else {{
        laneEnds[laneIdx] = seg.end;
      }}
      seg.lane = laneIdx;
    }});
    return laneEnds.length;
  }}

  function buildGanttBars(eqpId, windowStart, windowEnd) {{
    var busyRows = rowsForEqp(eqpId).filter(function (r) {{
      return r.start_time < windowEnd && r.end_time > windowStart;
    }});
    var segments = busyRows.map(function (r) {{
      return {{
        start: r.start_time < windowStart ? windowStart : r.start_time,
        end: r.end_time > windowEnd ? windowEnd : r.end_time,
        lot_id: r.lot_id
      }};
    }});
    var laneCount = greedyPackLanes(segments);
    if (laneCount === 0) {{ laneCount = 1; }}

    var byLane = {{}};
    segments.forEach(function (s) {{
      byLane[s.lane] = byLane[s.lane] || [];
      byLane[s.lane].push(s);
    }});

    var bars = [];
    for (var lane = 0; lane < laneCount; lane++) {{
      var segs = (byLane[lane] || []).slice().sort(function (a, b) {{ return a.start - b.start; }});
      var cursor = windowStart;
      segs.forEach(function (s) {{
        if (s.start > cursor) {{
          bars.push({{lane: lane, start: cursor, end: s.start, status: "{WAIT_STATUS}", lot_id: ""}});
        }}
        bars.push({{lane: lane, start: s.start, end: s.end, status: "{BUSY_STATUS}", lot_id: s.lot_id}});
        cursor = s.end;
      }});
      if (cursor < windowEnd) {{
        bars.push({{lane: lane, start: cursor, end: windowEnd, status: "{WAIT_STATUS}", lot_id: ""}});
      }}
    }}
    return bars;
  }}

  function buildWipSeries(eqpId, windowStart, windowEnd) {{
    var eqpRows = rowsForEqp(eqpId);
    var busyIntervals = eqpRows.map(function (r) {{ return {{start: r.start_time, end: r.end_time}}; }});
    var waitSelfIntervals = eqpRows
      .filter(function (r) {{ return r.wait_minutes != null && r.wait_minutes > 0; }})
      .map(function (r) {{
        var start = new Date(r.start_time.getTime() - r.wait_minutes * 60000);
        return {{start: start, end: r.start_time}};
      }});
    var waitOtherIntervals = [];
    eqpRows.forEach(function (r) {{
      if (r.next_eqp_id && r.next_eqp_id !== eqpId) {{
        var nextRow = BY_LOT_SEQ[r.lot_id + "|" + (r.ope_seq + 1)];
        if (nextRow) {{
          waitOtherIntervals.push({{start: r.end_time, end: nextRow.start_time}});
        }}
      }}
    }});

    function countAt(intervals, t) {{
      var n = 0;
      for (var i = 0; i < intervals.length; i++) {{
        if (intervals[i].start <= t && intervals[i].end > t) {{ n++; }}
      }}
      return n;
    }}

    var bucketMs = WIP_BUCKET_MINUTES * 60000;
    var times = [];
    var busyCounts = [];
    var waitSelfCounts = [];
    var waitOtherCounts = [];
    for (var t = windowStart.getTime(); t < windowEnd.getTime(); t += bucketMs) {{
      var bucketTime = new Date(t);
      times.push(bucketTime);
      busyCounts.push(countAt(busyIntervals, bucketTime));
      waitSelfCounts.push(countAt(waitSelfIntervals, bucketTime));
      waitOtherCounts.push(countAt(waitOtherIntervals, bucketTime));
    }}
    return {{times: times, busyCounts: busyCounts, waitSelfCounts: waitSelfCounts, waitOtherCounts: waitOtherCounts}};
  }}

  function renderStage3(eqpId, windowStart, windowEnd) {{
    var bars = buildGanttBars(eqpId, windowStart, windowEnd);
    var ganttTrace = {{
      type: "bar",
      orientation: "h",
      // base（bar固有の属性）はDateオブジェクトのままだと解釈されず、
      // 全区間がx=0起点になってしまう（回帰テスト参照）。ISO文字列で渡す。
      base: bars.map(function (b) {{ return b.start.toISOString(); }}),
      x: bars.map(function (b) {{ return b.end - b.start; }}),
      y: bars.map(function (b) {{ return b.lane; }}),
      text: bars.map(function (b) {{ return b.status === "{BUSY_STATUS}" ? b.lot_id : ""; }}),
      textposition: "inside",
      hovertext: bars.map(function (b) {{ return b.lot_id || ""; }}),
      marker: {{color: bars.map(function (b) {{ return b.status === "{BUSY_STATUS}" ? COLOR_BUSY : COLOR_WAIT; }})}},
      xaxis: "x", yaxis: "y",
      showlegend: false
    }};

    var wip = buildWipSeries(eqpId, windowStart, windowEnd);
    function areaTrace(name, values, color) {{
      return {{
        type: "scatter", mode: "lines", stackgroup: "1",
        line: {{shape: "hv", color: color}},
        name: name,
        x: wip.times.map(function (t) {{ return t.toISOString(); }}), y: values,
        xaxis: "x2", yaxis: "y2"
      }};
    }}
    var wipTraces = [
      areaTrace("{BUSY_STATUS}", wip.busyCounts, COLOR_BUSY),
      areaTrace("待機中(自装置着工)", wip.waitSelfCounts, COLOR_WAIT_SELF),
      areaTrace("待機中(他装置着工)", wip.waitOtherCounts, COLOR_WAIT_OTHER)
    ];

    var layout = {{
      // type:"date"を明示しないと、baseが日時でもxが数値(所要時間)のため
      // 自動判定されず、全区間がx=0起点で描かれてしまう
      // (gantt.pyの`add_gantt_traces()`と同じ対策)。
      xaxis: {{anchor: "y", domain: [0, 1], matches: "x2", showticklabels: false, type: "date"}},
      xaxis2: {{anchor: "y2", domain: [0, 1]}},
      yaxis: {{type: "category", domain: [0.58, 1.0], title: "並行処理枠", anchor: "x"}},
      yaxis2: {{domain: [0.0, 0.42], title: "仕掛数量", anchor: "x2"}},
      // barmode:"stack"は指定しない: ガント側は1トレース内で複数の区間が
      // 同じ行(y)を共有する構造のため、"stack"にするとPlotlyがそれらを
      // 累積的に積み上げてしまい、baseで指定した絶対位置が壊れる
      // (仕掛数量推移の面グラフはstackgroupで別途積み上げているので影響を受けない)。
      title: eqpId + " ガントチャート＋仕掛数量推移",
      showlegend: true,
      legend: {{orientation: "h", y: 0.52}}
    }};

    Plotly.react("stage3-chart", [ganttTrace].concat(wipTraces), layout);
  }}

  function clearStage4() {{
    document.getElementById("stage4-body").innerHTML = "";
    document.getElementById("stage4-hint").textContent = "まだロットが選択されていません。";
  }}

  return {{
    onStage1Select: function (eqpId) {{
      clearStage4();
    }},
    onStage2Select: function (eqpId, hourStartIso) {{
      var hourStartMs = new Date(hourStartIso).getTime();
      var windowStart = new Date(hourStartMs - (GANTT_WINDOW_HOURS / 2) * 3600000);
      var windowEnd = new Date(hourStartMs + (GANTT_WINDOW_HOURS / 2) * 3600000);
      renderStage3(eqpId, windowStart, windowEnd);
      clearStage4();
    }},
    onStage3Select: function (lotId) {{
      var rows = ALL_ROWS.filter(function (r) {{ return r.lot_id === lotId; }})
        .sort(function (a, b) {{ return a.ope_seq - b.ope_seq; }});
      var tbody = document.getElementById("stage4-body");
      tbody.innerHTML = "";
      var cols = window.LOT_DETAIL.columns;
      rows.forEach(function (row) {{
        var tr = document.createElement("tr");
        cols.forEach(function (c) {{
          var td = document.createElement("td");
          var v = row[c];
          td.textContent = (v instanceof Date) ? v.toISOString() : v;
          tr.appendChild(td);
        }});
        tbody.appendChild(tr);
      }});
      document.getElementById("stage4-hint").textContent = "ロット " + lotId + " の明細（" + rows.length + "件）";
    }}
  }};
}})();

window.EqpDrilldown.onStage2Select({default_eqp_id!r}, {default_hour_iso!r});
"""
