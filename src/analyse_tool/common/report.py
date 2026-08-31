"""棒グラフ等をクリックすると明細データを表示するレポートHTMLの共通組み立て処理。

「集計グラフを見て気になった棒をクリックすると、その内訳の明細行が
表を作る」というドリルダウンUIは複数ツールで再利用したいパターンのため、
`common/` に置く（`common/charts/` はグラフ種類ごとの Figure 生成に徹しているので、
グラフ＋表＋クリック連動JSまで含めた「レポート組み立て」はこちらに分離する）。

サーバー起動なしで `file://` でも開ける自己完結HTMLにするため、明細データは
JSONとしてHTMLに埋め込み、クリック時の絞り込みはブラウザ側のJSで行う。
数百万〜数億行規模の明細をまるごと埋め込む用途は想定していない
（`analyze.py` 側で表示対象を集計・抽出した後の、数千〜数万行程度の
小さい明細データを渡す前提）。

このモジュールはHTML文字列を組み立てるところまでを担い、ファイルへの
書き出しは行わない（ファイルI/Oは各ツールの `io.py` の責務にするため）。
"""

from __future__ import annotations

import json

import pandas as pd
import plotly.graph_objects as go


def build_bar_click_detail_html(
    fig: go.Figure,
    detail_df: pd.DataFrame,
    detail_match_columns: dict[str, str],
    title: str = "",
    max_detail_rows: int = 2000,
) -> str:
    """積み上げ棒グラフ + クリックで絞り込む明細表、を1枚のHTML文字列にまとめる。

    Args:
        fig: `common.charts.bar.stacked_bar()` などで作った棒グラフ。
            各トレースの `name` が色分け軸の値になっている前提
            （`stacked_bar()` はそのように作る）。
        detail_df: 明細データ（クリックで絞り込んで表示する行）。
        detail_match_columns: クリックした棒と明細行の対応付け。
            `{"x": 明細側の列名, "trace_name": 明細側の列名}` の形で指定する。
            `"x"` は棒グラフの横軸カテゴリ、`"trace_name"` はクリックした
            トレース名（= 色分け軸の値）に対応する。
        title: レポート全体のタイトル（`<title>` 及び見出しに使用）。
        max_detail_rows: 明細表に一度に表示する最大行数
            （それを超える場合は先頭 `max_detail_rows` 件のみ表示し、その旨を注記する）。

    Returns:
        自己完結HTML（`<!DOCTYPE html>` から）の文字列。呼び出し側の `io.py` が
        ファイルに書き出す。
    """
    fig_html = fig.to_html(full_html=False, include_plotlyjs="cdn", div_id="chart")
    detail_columns = list(detail_df.columns)
    detail_records = json.loads(detail_df.to_json(orient="records", force_ascii=False))
    match_config = {
        "x": detail_match_columns.get("x"),
        "trace_name": detail_match_columns.get("trace_name"),
    }

    return _TEMPLATE.format(
        title=_escape(title),
        fig_html=fig_html,
        detail_columns_json=json.dumps(detail_columns, ensure_ascii=False),
        detail_records_json=json.dumps(detail_records, ensure_ascii=False),
        match_config_json=json.dumps(match_config, ensure_ascii=False),
        max_detail_rows=max_detail_rows,
    )


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ font-family: -apple-system, "Hiragino Sans", "Yu Gothic", sans-serif; margin: 24px; }}
  h1 {{ font-size: 1.3em; }}
  #detail-hint {{ color: #666; margin: 8px 0; }}
  #detail-section {{ margin-top: 16px; }}
  table {{ border-collapse: collapse; font-size: 0.9em; }}
  th, td {{ border: 1px solid #ddd; padding: 4px 10px; text-align: left; }}
  th {{ background: #f4f4f4; position: sticky; top: 0; }}
  #detail-table-wrap {{ max-height: 480px; overflow: auto; border: 1px solid #eee; }}
  #detail-note {{ color: #888; font-size: 0.85em; margin-top: 4px; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div id="detail-hint">グラフの棒をクリックすると、その内訳の明細データが下に表示されます。</div>
{fig_html}
<div id="detail-section">
  <h2 id="detail-heading">明細データ</h2>
  <div id="detail-table-wrap">
    <table>
      <thead><tr id="detail-head-row"></tr></thead>
      <tbody id="detail-body"></tbody>
    </table>
  </div>
  <div id="detail-note"></div>
</div>
<script>
(function () {{
  const columns = {detail_columns_json};
  const records = {detail_records_json};
  const matchConfig = {match_config_json};
  const maxRows = {max_detail_rows};

  const headRow = document.getElementById("detail-head-row");
  columns.forEach(function (col) {{
    const th = document.createElement("th");
    th.textContent = col;
    headRow.appendChild(th);
  }});

  const heading = document.getElementById("detail-heading");
  const tbody = document.getElementById("detail-body");
  const note = document.getElementById("detail-note");

  function renderDetail(xValue, traceName) {{
    const xCol = matchConfig.x;
    const traceCol = matchConfig.trace_name;
    const matched = records.filter(function (row) {{
      const xOk = !xCol || String(row[xCol]) === String(xValue);
      const traceOk = !traceCol || String(row[traceCol]) === String(traceName);
      return xOk && traceOk;
    }});

    heading.textContent = "明細データ（" + xValue + " / " + traceName + "： " + matched.length + "件）";
    tbody.innerHTML = "";
    matched.slice(0, maxRows).forEach(function (row) {{
      const tr = document.createElement("tr");
      columns.forEach(function (col) {{
        const td = document.createElement("td");
        td.textContent = row[col];
        tr.appendChild(td);
      }});
      tbody.appendChild(tr);
    }});

    note.textContent = matched.length > maxRows
      ? "先頭 " + maxRows + " 件のみ表示しています（全 " + matched.length + " 件）。"
      : "";
  }}

  const chartDiv = document.getElementById("chart");
  chartDiv.on("plotly_click", function (eventData) {{
    const point = eventData.points[0];
    renderDetail(point.x, point.data.name);
  }});
}})();
</script>
</body>
</html>
"""


def build_multi_stage_drilldown_html(
    *,
    title: str,
    lead_sections_html: list[str],
    stage1_fig: go.Figure,
    stage1_heading: str,
    stage2_figs: dict[str, go.Figure],
    stage2_default_key: str,
    stage2_heading: str,
    stage3_default_fig: go.Figure,
    stage3_heading: str,
    stage3_curve_number: int,
    stage4_heading: str,
    lot_detail_columns: list[str],
    lot_detail_data: dict[str, list[object]],
    domain_js: str,
    disclaimer: str = "",
) -> str:
    """パレート図→段2→段3→段4、と数珠つなぎにクリックが連動する
    レポートHTML文字列を組み立てる（N段クリック連動）。

    段によって鍵の候補数が大きく異なる（例: 設備は上位15台だが、
    設備×時間帯は数百〜千通り）ため、2つのメカニズムを使い分ける。

    - **選択式**（段1→段2）: 呼び出し側が候補ぶん全ての`go.Figure`を
      事前レンダリングして`stage2_figs`に渡す。クリックは表示/非表示の
      切り替えのみで、新たな`go.Figure`は作らない。
    - **構築式**（段2→段3、段3→段4）: 候補数が多すぎるため、
      `domain_js`（呼び出し側が組み立てるドメイン固有のJavaScript）が
      `lot_detail_data`（絞り込み済みの明細データ、columnar JSON）から
      都度チャート・表を構築する。このモジュール自身はドメイン知識
      （何を集計するか・どう色分けするか等）を一切持たない。

    Args:
        title: レポート全体のタイトル。
        lead_sections_html: 常時表示するセクション（①〜⑤等）のHTML
            断片のリスト。それぞれ`fig.to_html(include_plotlyjs=False)`
            で作った文字列を想定。
        stage1_fig: 段1（パレート図）の`go.Figure`。棒をクリックすると
            段2が切り替わる。
        stage1_heading: 段1の見出し文字列。
        stage2_figs: 段2の候補ぶん全ての`go.Figure`（キー＝クリック時の
            `x`値と一致させる文字列。例: `eqp_id`）。
        stage2_default_key: 初期表示する`stage2_figs`のキー。
        stage2_heading: 段2の見出し文字列。
        stage3_default_fig: 段3の初期表示用`go.Figure`
            （`stage2_default_key`に対応する代表的な絞り込み）。
        stage3_heading: 段3の見出し文字列。
        stage3_curve_number: 段3の中で「クリックされたら段4に進める」
            トレースの`curveNumber`（例: `twograph.py`のガント側）。
        stage4_heading: 段4（明細表）の見出し文字列。
        lot_detail_columns: 段3・段4を構築するための明細データの列名。
        lot_detail_data: 明細データ本体（`{列名: [値, ...]}`のcolumnar
            形式。records形式より埋め込みサイズが小さい）。
        domain_js: `window.EqpDrilldown`にドメイン固有の関数
            （段2クリック時に段3を再構築する関数・段3クリック時に段4を
            再構築する関数）を定義するJavaScript文字列。呼び出し側
            （`visualize.py`）が組み立てて渡す。このモジュールは中身を
            解釈せず、そのまま埋め込む。
        disclaimer: 画面上部に表示する注記（省略可）。

    Returns:
        自己完結HTML（`<!DOCTYPE html>`から）の文字列。
    """
    lead_html = "\n".join(lead_sections_html)

    stage1_html = stage1_fig.to_html(
        full_html=False, include_plotlyjs=False, div_id="stage1-pareto"
    )

    stage2_html_parts = []
    for key, fig in stage2_figs.items():
        display = "block" if key == stage2_default_key else "none"
        fig_html = fig.to_html(
            full_html=False, include_plotlyjs=False, div_id=f"stage2-{_dom_id(key)}"
        )
        stage2_html_parts.append(
            f'<div class="stage2-fig" data-key="{_escape(key)}" style="display:{display};">'
            f"{fig_html}</div>"
        )
    stage2_html = "\n".join(stage2_html_parts)

    stage3_html = stage3_default_fig.to_html(
        full_html=False, include_plotlyjs=False, div_id="stage3-chart"
    )

    return _MULTI_STAGE_TEMPLATE.format(
        title=_escape(title),
        disclaimer_html=f'<div id="disclaimer">{_escape(disclaimer)}</div>'
        if disclaimer
        else "",
        lead_html=lead_html,
        stage1_heading=_escape(stage1_heading),
        stage1_html=stage1_html,
        stage2_heading=_escape(stage2_heading),
        stage2_html=stage2_html,
        stage3_heading=_escape(stage3_heading),
        stage3_html=stage3_html,
        stage3_curve_number=stage3_curve_number,
        stage4_heading=_escape(stage4_heading),
        lot_detail_columns_json=json.dumps(lot_detail_columns, ensure_ascii=False),
        lot_detail_data_json=json.dumps(
            lot_detail_data, ensure_ascii=False, default=str
        ),
        domain_js=domain_js,
    )


def _dom_id(key: str) -> str:
    """キー文字列をHTMLのid属性に使える形にする（英数字・`_`・`-`以外を置換）。"""
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in key)


_MULTI_STAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="https://cdn.plot.ly/plotly-3.0.1.min.js"></script>
<style>
  body {{ font-family: -apple-system, "Hiragino Sans", "Yu Gothic", sans-serif; margin: 24px; }}
  h1 {{ font-size: 1.4em; }}
  h2 {{ font-size: 1.1em; margin-top: 32px; border-top: 1px solid #ddd; padding-top: 16px; }}
  section {{ margin-bottom: 8px; }}
  #disclaimer {{ background: #fff8e1; border: 1px solid #ffe082; padding: 8px 12px;
                 font-size: 0.85em; color: #6b5600; margin-bottom: 16px; }}
  .hint {{ color: #666; font-size: 0.85em; margin: 4px 0; }}
  table {{ border-collapse: collapse; font-size: 0.9em; }}
  th, td {{ border: 1px solid #ddd; padding: 4px 10px; text-align: left; }}
  th {{ background: #f4f4f4; position: sticky; top: 0; }}
  #stage4-table-wrap {{ max-height: 480px; overflow: auto; border: 1px solid #eee; }}
</style>
</head>
<body>
<h1>{title}</h1>
{disclaimer_html}
{lead_html}

<h2>{stage1_heading}</h2>
<div class="hint">棒をクリックすると、その設備の「{stage2_heading}」が下に表示されます。</div>
{stage1_html}

<h2>{stage2_heading}</h2>
<div class="hint">1時間分の棒をクリックすると、その時間帯を中心にした「{stage3_heading}」が下に表示されます。</div>
<div id="stage2-container">
{stage2_html}
</div>

<h2>{stage3_heading}</h2>
<div class="hint">着工中区間（色付きの区間）をクリックすると、そのロットの「{stage4_heading}」が下に表示されます。</div>
{stage3_html}

<h2>{stage4_heading}</h2>
<div id="stage4-hint" class="hint">まだロットが選択されていません。</div>
<div id="stage4-table-wrap">
  <table>
    <thead><tr id="stage4-head-row"></tr></thead>
    <tbody id="stage4-body"></tbody>
  </table>
</div>

<script>
window.LOT_DETAIL = {{
  columns: {lot_detail_columns_json},
  data: {lot_detail_data_json}
}};
window.STAGE3_CURVE_NUMBER = {stage3_curve_number};

{domain_js}

(function () {{
  // 段1→段2: 選択式（表示/非表示の切り替えのみ、新たなFigureは作らない）
  const stage1Div = document.getElementById("stage1-pareto");
  stage1Div.on("plotly_click", function (eventData) {{
    const key = String(eventData.points[0].x);
    document.querySelectorAll(".stage2-fig").forEach(function (el) {{
      el.style.display = el.dataset.key === key ? "block" : "none";
    }});
    window.EqpDrilldown.onStage1Select(key);
  }});

  // 段2→段3: 構築式（クリックされた棒の設備・時間帯からドメインJSが再構築する）
  document.querySelectorAll(".stage2-fig").forEach(function (wrapper) {{
    const eqpId = wrapper.dataset.key;
    const plotDiv = wrapper.querySelector(".plotly-graph-div");
    plotDiv.on("plotly_click", function (eventData) {{
      const hourStart = eventData.points[0].x;
      window.EqpDrilldown.onStage2Select(eqpId, hourStart);
    }});
  }});

  // 段3→段4: 構築式（ガント側のcurveNumberのみを段4に進める対象とする）
  const stage3Div = document.getElementById("stage3-chart");
  stage3Div.on("plotly_click", function (eventData) {{
    const point = eventData.points[0];
    if (point.curveNumber !== window.STAGE3_CURVE_NUMBER) {{
      return;
    }}
    const lotId = point.hovertext;
    if (!lotId) {{
      return;
    }}
    window.EqpDrilldown.onStage3Select(lotId);
  }});

  const headRow = document.getElementById("stage4-head-row");
  window.LOT_DETAIL.columns.forEach(function (col) {{
    const th = document.createElement("th");
    th.textContent = col;
    headRow.appendChild(th);
  }});
}})();
</script>
</body>
</html>
"""
