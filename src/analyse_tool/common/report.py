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
