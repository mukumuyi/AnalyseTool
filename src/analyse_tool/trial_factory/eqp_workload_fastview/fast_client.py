"""⑥-2〜⑥-4のブラウザ側ロジック（日クリック→取得→Canvas描画→明細更新）。

`common/report.py`の多段ドリルダウン機構（構築式／選択式）は「全データが
埋め込み済みで、クリックのたびに同期的に絞り込む」という前提のため、
非同期`fetch()`を挟む本ツールには使わない
（`.steering/20260901-eqp-workload-fastview/design.md`の「課題対応」
参照）。`visualize.py`の肥大化を避けるため、このモジュールでJS文字列の
組み立てを引き受ける（`visualize.py`は「どこに何を置くか」だけを決める
薄い調整役に徹する）。

JSテンプレートは`string.Template`の`$identifier`置換を使う（f-stringだと
JS側の`{}`をすべて`{{`/`}}`にエスケープする必要があり、この分量では
読みにくく壊れやすいため）。
"""

from __future__ import annotations

import json
from string import Template
from typing import Any

GANTT_CANVAS_ID = "gantt-canvas"
WIP_CANVAS_ID = "wip-canvas"
WIP_AXIS_ID = "wip-axis"
LABEL_COLUMN_ID = "gantt-labels"
AXIS_ID = "gantt-axis"
TOOLTIP_ID = "gantt-tooltip"
STAGE3_HEADING_ID = "stage3-heading-date"
STAGE4_HINT_ID = "stage4-hint"
STAGE4_BODY_ID = "stage4-body"
DAILY_CHART_DIV_ID = "stage2-daily-chart"

# 縦方向のページスクロールが多いというユーザー指摘（2026-09-02）を受け、
# 全体の縦寸法が旧値（22/3/8）のおよそ1/4になるよう縮小した。
ROW_HEIGHT_PX = 5
ROW_GAP_PX = 1
EQP_GAP_PX = 2


def build_fast_client_js(
    *,
    data_base_url: str,
    initial_date: str,
    initial_day_payload: dict[str, Any],
    single_file: bool,
    color_busy: str,
    color_wait: str,
    color_status_processing: str,
    color_status_waiting: str,
) -> str:
    """⑥-2〜⑥-4を動かすJS文字列を組み立てる。

    Args:
        data_base_url: 日別JSON（`data/days/<日付>.json`）へのベースURL
            （`index.html`からの相対パス。例: `"data/days/"`）。
        initial_date: 初期表示する日（`YYYY-MM-DD`）。
        initial_day_payload: `initial_date`の⑥-3/⑥-4ペイロード
            （初回描画・単一HTML版はこれだけを使う）。
        single_file: `True`の場合`fetch()`を行わず、`initial_date`以外が
            クリックされたら「高速モードで起動してください」という注記を
            出すだけにする。
        color_busy, color_wait: ⑥-3ガントの区間バー、および⑥-3仕掛数量
            推移の着工中／待機中の帯の配色（16進カラーコード）。
        color_status_processing, color_status_waiting: ⑥-3ガントの
            設備ごとの背景色（装置ステータス。稼働中／待機中）。区間バー
            の視認性を保つため、`color_busy`より淡い色を想定する。

    Returns:
        `window.FastView`を定義し、初期日を描画するJS文字列。
        `common/report.py`は経由せず、`visualize.py`が組み立てるシェル
        HTMLへそのまま埋め込む。⑥-3ガントはホイールでズーム、ドラッグで
        パン、ダブルクリックで全期間表示へリセットできる。仕掛数量推移
        グラフもガントと同じ表示範囲（時間軸）に同期する（縦軸のスケール
        は1日全体の最大値で固定し、ズームしても縦方向の見た目は変えない）。
    """
    return _TEMPLATE.substitute(
        data_base_url_json=json.dumps(data_base_url),
        initial_date_json=json.dumps(initial_date),
        initial_payload_json=json.dumps(
            initial_day_payload, ensure_ascii=False, default=str
        ),
        single_file_json=json.dumps(bool(single_file)),
        color_busy_json=json.dumps(color_busy),
        color_wait_json=json.dumps(color_wait),
        color_status_processing_json=json.dumps(color_status_processing),
        color_status_waiting_json=json.dumps(color_status_waiting),
        gantt_canvas_id_json=json.dumps(GANTT_CANVAS_ID),
        wip_canvas_id_json=json.dumps(WIP_CANVAS_ID),
        wip_axis_id_json=json.dumps(WIP_AXIS_ID),
        label_column_id_json=json.dumps(LABEL_COLUMN_ID),
        axis_id_json=json.dumps(AXIS_ID),
        tooltip_id_json=json.dumps(TOOLTIP_ID),
        stage3_heading_id_json=json.dumps(STAGE3_HEADING_ID),
        stage4_hint_id_json=json.dumps(STAGE4_HINT_ID),
        stage4_body_id_json=json.dumps(STAGE4_BODY_ID),
        daily_chart_div_id_json=json.dumps(DAILY_CHART_DIV_ID),
        row_height=ROW_HEIGHT_PX,
        row_gap=ROW_GAP_PX,
        eqp_gap=EQP_GAP_PX,
    )


_TEMPLATE = Template(
    """
window.FastView = (function () {
  "use strict";
  var DATA_BASE_URL = $data_base_url_json;
  var INITIAL_DATE = $initial_date_json;
  var INITIAL_PAYLOAD = $initial_payload_json;
  var SINGLE_FILE = $single_file_json;
  var COLOR_BUSY = $color_busy_json;
  var COLOR_WAIT = $color_wait_json;
  var STATUS_PROCESSING_BG = $color_status_processing_json;
  var STATUS_WAITING_BG = $color_status_waiting_json;
  var ROW_H = $row_height;
  var ROW_GAP = $row_gap;
  var EQP_GAP = $eqp_gap;

  // ⑥-3ズーム・スクロール用の定数（.steering/20260901-eqp-workload-fastview/
  // design.mdの「追加設計」参照）。
  var DAY_MIN = 1440; // 1日の分数（00:00〜翌日00:00）
  var MIN_WINDOW_MIN = 30; // ズームインの下限（表示幅30分まで）
  var MAX_WINDOW_MIN = DAY_MIN; // ズームアウトの上限（1日分＝初期表示）
  var ZOOM_FACTOR = 1.2; // ホイール1回あたりの拡大・縮小倍率
  var DRAG_THRESHOLD_PX = 4; // これを超えて動いたらクリックでなくパンとみなす
  var TICK_CANDIDATES_MIN = [5, 10, 15, 30, 60, 120, 240, 360, 720, 1440];

  var ganttCanvas = document.getElementById($gantt_canvas_id_json);
  var wipCanvas = document.getElementById($wip_canvas_id_json);
  var wipAxisEl = document.getElementById($wip_axis_id_json);
  var labelColumn = document.getElementById($label_column_id_json);
  var axisEl = document.getElementById($axis_id_json);
  var tooltip = document.getElementById($tooltip_id_json);
  var headingDateEl = document.getElementById($stage3_heading_id_json);
  var stage4Hint = document.getElementById($stage4_hint_id_json);
  var stage4Body = document.getElementById($stage4_body_id_json);

  var dayCache = {};
  dayCache[INITIAL_DATE] = INITIAL_PAYLOAD;
  var requestSeq = 0;
  var hitList = []; // {x, y, w, h, lotId} 直近描画分（クリック・ホバー判定用）
  var currentPayload = null;
  var viewStart = 0; // ⑥-3の現在の表示範囲（日内の分、ズーム・パンで変化）
  var viewEnd = DAY_MIN;
  var isDragging = false; // マウスボタン押下中か
  var didPan = false; // 押下中に閾値を超えて動き、パンとみなされたか
  var dragStartClientX = 0;
  var dragStartView = null;

  function fmtMin(min) {
    var m = ((Math.round(min) % 1440) + 1440) % 1440;
    var h = Math.floor(m / 60);
    var mm = m % 60;
    return (h < 10 ? "0" + h : h) + ":" + (mm < 10 ? "0" + mm : mm);
  }

  function groupByEqp(segments) {
    var byEqp = {};
    var n = segments.eqp_id ? segments.eqp_id.length : 0;
    for (var i = 0; i < n; i++) {
      var eqpId = segments.eqp_id[i];
      (byEqp[eqpId] = byEqp[eqpId] || []).push({
        lane: segments.lane[i],
        start_min: segments.start_min[i],
        end_min: segments.end_min[i],
        lot_id: segments.lot_id[i]
      });
    }
    return byEqp;
  }

  function pickTickStepMin(rangeMin) {
    // 目盛本数がおおむね4〜10本に収まる最小の候補間隔を選ぶ。
    for (var i = 0; i < TICK_CANDIDATES_MIN.length; i++) {
      var step = TICK_CANDIDATES_MIN[i];
      if (rangeMin / step <= 10) { return step; }
    }
    return TICK_CANDIDATES_MIN[TICK_CANDIDATES_MIN.length - 1];
  }

  function ticksInView() {
    var step = pickTickStepMin(viewEnd - viewStart);
    var first = Math.ceil(viewStart / step) * step;
    var ticks = [];
    for (var t = first; t <= viewEnd; t += step) { ticks.push(t); }
    return ticks;
  }

  function fmtAxisTick(min) {
    // 日境界（1440分＝翌日00:00）はfmtMin()だと"00:00"に丸まり先頭の
    // 目盛と見分けが付かなくなるため、目盛表示だけは"24:00"のままにする。
    if (min >= DAY_MIN) { return "24:00"; }
    return fmtMin(min);
  }

  function renderAxis() {
    axisEl.innerHTML = ticksInView().map(function (t) {
      var leftPct = ((t - viewStart) / (viewEnd - viewStart)) * 100;
      return "<span style=\\"left:" + leftPct.toFixed(4) + "%;\\">" + fmtAxisTick(t) + "</span>";
    }).join("");
  }

  function clampWindowWidth(width) {
    if (width < MIN_WINDOW_MIN) { return MIN_WINDOW_MIN; }
    if (width > MAX_WINDOW_MIN) { return MAX_WINDOW_MIN; }
    return width;
  }

  function setView(start, width) {
    width = clampWindowWidth(width);
    if (start < 0) { start = 0; }
    if (start + width > DAY_MIN) { start = DAY_MIN - width; }
    viewStart = start;
    viewEnd = start + width;
  }

  function zoomAt(cursorMin, factor) {
    var oldWidth = viewEnd - viewStart;
    var newWidth = clampWindowWidth(oldWidth / factor);
    var ratio = oldWidth <= 0 ? 0.5 : (cursorMin - viewStart) / oldWidth;
    setView(cursorMin - ratio * newWidth, newWidth);
    renderGantt(currentPayload);
    renderAxis();
    renderWip(currentPayload); // 仕掛数量推移もガントと同じ表示範囲に同期させる
  }

  function mergeIntervals(pairs) {
    // [start, end]の配列を開始時刻順に結合し、重なり・隣接区間をまとめる。
    // 装置ステータス（稼働中/待機中）の背景色分けに使う：ロットが1件でも
    // 進行中なら稼働中とみなすため、区間同士の重なりは単純に和で良い。
    var sorted = pairs.slice().sort(function (a, b) { return a[0] - b[0]; });
    var merged = [];
    for (var i = 0; i < sorted.length; i++) {
      var cur = sorted[i];
      var last = merged.length ? merged[merged.length - 1] : null;
      if (last && cur[0] <= last[1]) {
        if (cur[1] > last[1]) { last[1] = cur[1]; }
      } else {
        merged.push([cur[0], cur[1]]);
      }
    }
    return merged;
  }

  function renderGantt(payload) {
    var eqpIds = payload.eqp_ids || [];
    var byEqp = groupByEqp(payload.segments || {});
    var laneCounts = eqpIds.map(function (id) {
      var segs = byEqp[id] || [];
      var maxLane = -1;
      segs.forEach(function (s) { if (s.lane > maxLane) { maxLane = s.lane; } });
      return maxLane + 1 || 1;
    });

    var rowYStarts = [];
    var y = 0;
    eqpIds.forEach(function (id, i) {
      rowYStarts.push(y);
      y += laneCounts[i] * (ROW_H + ROW_GAP) + EQP_GAP;
    });
    var totalHeight = Math.max(y, 1);

    var width = ganttCanvas.clientWidth || 800;
    var dpr = window.devicePixelRatio || 1;
    ganttCanvas.width = width * dpr;
    ganttCanvas.height = totalHeight * dpr;
    ganttCanvas.style.height = totalHeight + "px";
    var ctx = ganttCanvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, totalHeight);

    // 装置ステータス背景（稼働中/待機中）。ロットが1件でも着工していれば
    // 稼働中、無ければ待機中（区間バーより先に描いて背後に敷く）。
    // 将来「停止(stop)」ステータスを追加する場合も、この時間区間リストに
    // 第三の状態を割り当てる形で拡張できる想定（現状は2値のみ）。
    var viewWidth = viewEnd - viewStart;
    eqpIds.forEach(function (id, i) {
      var segs = byEqp[id] || [];
      var processingIntervals = mergeIntervals(
        segs.map(function (s) { return [s.start_min, s.end_min]; })
      );
      var rowTop = rowYStarts[i];
      var rowHeight = laneCounts[i] * (ROW_H + ROW_GAP);
      ctx.fillStyle = STATUS_WAITING_BG;
      ctx.fillRect(0, rowTop, width, rowHeight);
      ctx.fillStyle = STATUS_PROCESSING_BG;
      processingIntervals.forEach(function (iv) {
        if (iv[1] <= viewStart || iv[0] >= viewEnd) { return; } // 画面外は描画しない
        var ivX = ((iv[0] - viewStart) / viewWidth) * width;
        var ivW = ((iv[1] - iv[0]) / viewWidth) * width;
        ctx.fillRect(ivX, rowTop, ivW, rowHeight);
      });
    });

    // 目盛線（間隔はrenderAxis()と同じticksInView()を使い表示範囲に追従する）
    ctx.strokeStyle = "rgba(120,130,140,0.25)";
    ctx.lineWidth = 1;
    ticksInView().forEach(function (t) {
      var gx = Math.round(((t - viewStart) / viewWidth) * width) + 0.5;
      ctx.beginPath();
      ctx.moveTo(gx, 0);
      ctx.lineTo(gx, totalHeight);
      ctx.stroke();
    });

    hitList = [];
    labelColumn.innerHTML = "";
    eqpIds.forEach(function (id, i) {
      var label = document.createElement("div");
      label.className = "gantt-label-row";
      label.style.height = (laneCounts[i] * (ROW_H + ROW_GAP) + EQP_GAP) + "px";
      label.title = id + "（サブレーン " + laneCounts[i] + "）"; // 縦を詰めたため、サブレーン数はホバーでのみ表示する
      label.textContent = id;
      labelColumn.appendChild(label);

      var segs = (byEqp[id] || []).slice().sort(function (a, b) { return a.start_min - b.start_min; });
      segs.forEach(function (s) {
        if (s.end_min <= viewStart || s.start_min >= viewEnd) { return; } // 画面外は描画しない
        var x = ((s.start_min - viewStart) / viewWidth) * width;
        var w = Math.max(1, ((s.end_min - s.start_min) / viewWidth) * width);
        var yTop = rowYStarts[i] + s.lane * (ROW_H + ROW_GAP);
        var isBusy = !!s.lot_id;
        ctx.fillStyle = isBusy ? COLOR_BUSY : COLOR_WAIT;
        ctx.fillRect(x, yTop, w, ROW_H);
        if (isBusy) {
          hitList.push({
            x: x, y: yTop, w: w, h: ROW_H,
            eqpId: id, lotId: s.lot_id, startMin: s.start_min, endMin: s.end_min
          });
        }
      });
    });
  }

  function renderWipAxisLabels(maxTotal) {
    // 0・中間・最大値の3点だけ示す簡易な数値軸（wip-canvasの高さに揃えた
    // position:absoluteのHTML要素。Canvas内に文字を描くより鮮明に出せる）。
    var mid = Math.round(maxTotal / 2);
    var ticks = maxTotal <= 1 ? [0, maxTotal] : [0, mid, maxTotal];
    wipAxisEl.innerHTML = ticks.map(function (v) {
      var topPct = 100 - (v / maxTotal) * 100;
      return "<span style=\\"top:" + topPct.toFixed(2) + "%;\\">" + v + "</span>";
    }).join("");
  }

  function renderWip(payload) {
    var wip = payload.wip || { t_min: [], busy: [], wait: [] };
    var n = wip.t_min.length;
    var width = wipCanvas.clientWidth || 800;
    var height = wipCanvas.clientHeight || 90;
    var dpr = window.devicePixelRatio || 1;
    wipCanvas.width = width * dpr;
    wipCanvas.height = height * dpr;
    var ctx = wipCanvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);
    if (n === 0) { renderWipAxisLabels(1); return; }

    // 表示範囲（ズーム・パン）はガントと同期させ、常に⑥-3と同じ時間帯を
    // 表示する。縦軸のスケール（maxTotal）は1日全体の最大値で固定し、
    // ズームのたびに縦方向の見た目が変わらないようにする（1日全体に対する
    // 相対的な多さを保ったまま拡大できる）。
    var viewWidth = viewEnd - viewStart;
    var maxTotal = 1;
    for (var i = 0; i < n; i++) {
      var total = wip.busy[i] + wip.wait[i];
      if (total > maxTotal) { maxTotal = total; }
    }
    renderWipAxisLabels(maxTotal);

    // 目盛線（ガントの目盛と同じ間隔・同じ表示範囲で揃える）
    ctx.strokeStyle = "rgba(120,130,140,0.2)";
    ctx.lineWidth = 1;
    ticksInView().forEach(function (t) {
      var gx = Math.round(((t - viewStart) / viewWidth) * width) + 0.5;
      ctx.beginPath();
      ctx.moveTo(gx, 0);
      ctx.lineTo(gx, height);
      ctx.stroke();
    });

    function bandPath(getTop, getBottom) {
      ctx.beginPath();
      for (var i = 0; i < n; i++) {
        var x = ((wip.t_min[i] - viewStart) / viewWidth) * width;
        var yTop = height - (getTop(i) / maxTotal) * height;
        if (i === 0) { ctx.moveTo(x, yTop); } else { ctx.lineTo(x, yTop); }
      }
      for (var j = n - 1; j >= 0; j--) {
        var xj = ((wip.t_min[j] - viewStart) / viewWidth) * width;
        var yBottom = height - (getBottom(j) / maxTotal) * height;
        ctx.lineTo(xj, yBottom);
      }
      ctx.closePath();
    }

    var cumBusy = wip.busy;
    var cumTotal = wip.busy.map(function (v, i) { return v + wip.wait[i]; });

    ctx.fillStyle = COLOR_WAIT;
    bandPath(function (i) { return cumTotal[i]; }, function (i) { return cumBusy[i]; });
    ctx.fill();
    ctx.fillStyle = COLOR_BUSY;
    bandPath(function (i) { return cumBusy[i]; }, function () { return 0; });
    ctx.fill();
  }

  function clearStage4() {
    stage4Hint.textContent = "まだロットが選択されていません。";
    stage4Body.innerHTML = "";
  }

  function renderStage4(lotId, payload) {
    var detail = payload.lot_detail || {};
    var cols = detail.columns || [];
    var data = detail.data || {};
    var n = cols.length ? (data[cols[0]] || []).length : 0;
    var rows = [];
    for (var i = 0; i < n; i++) {
      if (data.lot_id[i] === lotId) {
        var row = {};
        cols.forEach(function (c) { row[c] = data[c][i]; });
        rows.push(row);
      }
    }
    rows.sort(function (a, b) { return a.ope_seq - b.ope_seq; });

    stage4Body.innerHTML = "";
    rows.forEach(function (row) {
      var tr = document.createElement("tr");
      cols.forEach(function (c) {
        var td = document.createElement("td");
        td.textContent = row[c];
        tr.appendChild(td);
      });
      stage4Body.appendChild(tr);
    });
    stage4Hint.textContent = "ロット " + lotId + " の明細（" + rows.length + "件）";
  }

  function applyPayload(payload) {
    currentPayload = payload;
    setView(0, DAY_MIN); // 日切替のたびにズーム・パン状態をリセットする
    headingDateEl.textContent = payload.date;
    renderGantt(payload);
    renderAxis();
    renderWip(payload);
    clearStage4();
  }

  function findHit(evt) {
    var rect = ganttCanvas.getBoundingClientRect();
    var x = evt.clientX - rect.left;
    var y = evt.clientY - rect.top;
    for (var i = 0; i < hitList.length; i++) {
      var h = hitList[i];
      if (x >= h.x && x <= h.x + h.w && y >= h.y && y <= h.y + h.h) {
        return h;
      }
    }
    return null;
  }

  function showUnavailableNotice(dateStr) {
    headingDateEl.textContent = dateStr + "（高速モードで起動すると表示できます）";
  }

  function selectDay(dateStr) {
    if (dayCache[dateStr]) {
      applyPayload(dayCache[dateStr]);
      return;
    }
    if (SINGLE_FILE) {
      showUnavailableNotice(dateStr);
      return;
    }
    requestSeq += 1;
    var myRequest = requestSeq;
    fetch(DATA_BASE_URL + dateStr + ".json")
      .then(function (res) {
        if (!res.ok) { throw new Error("day data not found: " + dateStr); }
        return res.json();
      })
      .then(function (payload) {
        // 連続して別日をクリックした場合、最後の要求以外の結果は破棄する
        if (myRequest !== requestSeq) { return; }
        dayCache[dateStr] = payload;
        applyPayload(payload);
      })
      .catch(function () {
        if (myRequest !== requestSeq) { return; }
        headingDateEl.textContent = dateStr + "（取得に失敗しました）";
      });
  }

  ganttCanvas.addEventListener("mousemove", function (evt) {
    if (isDragging) { return; } // パン中はホバー表示しない
    var hit = findHit(evt);
    if (!hit) {
      tooltip.style.opacity = "0";
      ganttCanvas.style.cursor = "grab"; // 既定はドラッグ可能を示すカーソル
      return;
    }
    ganttCanvas.style.cursor = "pointer";
    tooltip.style.opacity = "1";
    tooltip.style.left = evt.clientX + "px";
    tooltip.style.top = (evt.clientY - 8) + "px";
    tooltip.textContent = hit.eqpId + "  " + fmtMin(hit.startMin) + "–" + fmtMin(hit.endMin);
  });
  ganttCanvas.addEventListener("mouseleave", function () {
    tooltip.style.opacity = "0";
  });
  ganttCanvas.addEventListener("click", function (evt) {
    if (didPan) { return; } // ドラッグでパンした直後のクリックはロット選択とみなさない
    var hit = findHit(evt);
    if (hit && currentPayload) {
      renderStage4(hit.lotId, currentPayload);
    }
  });
  window.addEventListener("resize", function () {
    if (currentPayload) { renderGantt(currentPayload); renderWip(currentPayload); }
  });

  // --- ⑥-3ズーム（ホイール）・パン（ドラッグ）・リセット（ダブルクリック） ---
  ganttCanvas.addEventListener("wheel", function (evt) {
    if (!currentPayload) { return; }
    evt.preventDefault();
    var rect = ganttCanvas.getBoundingClientRect();
    var xRatio = rect.width > 0 ? (evt.clientX - rect.left) / rect.width : 0.5;
    var cursorMin = viewStart + xRatio * (viewEnd - viewStart);
    zoomAt(cursorMin, evt.deltaY < 0 ? ZOOM_FACTOR : 1 / ZOOM_FACTOR);
  }, { passive: false });

  ganttCanvas.addEventListener("mousedown", function (evt) {
    if (!currentPayload) { return; }
    isDragging = true;
    didPan = false;
    dragStartClientX = evt.clientX;
    dragStartView = { start: viewStart, end: viewEnd };
  });
  window.addEventListener("mousemove", function (evt) {
    if (!isDragging || !dragStartView) { return; }
    var dx = evt.clientX - dragStartClientX;
    if (!didPan && Math.abs(dx) < DRAG_THRESHOLD_PX) { return; }
    didPan = true;
    tooltip.style.opacity = "0";
    ganttCanvas.style.cursor = "grabbing";
    var rect = ganttCanvas.getBoundingClientRect();
    var width = dragStartView.end - dragStartView.start;
    var minPerPx = rect.width > 0 ? width / rect.width : 0;
    setView(dragStartView.start - dx * minPerPx, width);
    renderGantt(currentPayload);
    renderAxis();
    renderWip(currentPayload); // 仕掛数量推移もガントと同じ表示範囲に同期させる
  });
  window.addEventListener("mouseup", function () {
    isDragging = false;
    dragStartView = null;
    ganttCanvas.style.cursor = "grab";
  });
  ganttCanvas.addEventListener("dblclick", function () {
    if (!currentPayload) { return; }
    setView(0, DAY_MIN);
    renderGantt(currentPayload);
    renderAxis();
    renderWip(currentPayload); // 仕掛数量推移もガントと同じ表示範囲に同期させる
  });

  return { selectDay: selectDay };
})();

window.FastView.selectDay($initial_date_json);
"""
)
