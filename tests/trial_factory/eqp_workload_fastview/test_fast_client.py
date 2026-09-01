from analyse_tool.trial_factory.eqp_workload_fastview.fast_client import (
    AXIS_ID,
    DAILY_CHART_DIV_ID,
    GANTT_CANVAS_ID,
    STAGE4_BODY_ID,
    TOOLTIP_ID,
    WIP_AXIS_ID,
    WIP_CANVAS_ID,
    build_fast_client_js,
)


def _build(**overrides):
    defaults = {
        "data_base_url": "data/days/",
        "initial_date": "2026-03-01",
        "initial_day_payload": {"date": "2026-03-01", "eqp_ids": ["E1"]},
        "single_file": False,
        "color_busy": "#1f77b4",
        "color_wait": "#d3d3d3",
        "color_status_processing": "#dceefb",
        "color_status_waiting": "#eef0f2",
    }
    defaults.update(overrides)
    return build_fast_client_js(**defaults)


def test_build_fast_client_js_embeds_fetch_base_url_and_initial_date():
    js = _build()

    assert '"data/days/"' in js
    assert '"2026-03-01"' in js
    assert "fetch(DATA_BASE_URL + dateStr" in js


def test_build_fast_client_js_embeds_initial_payload_for_first_paint():
    js = _build(initial_day_payload={"date": "2026-03-01", "eqp_ids": ["EQP009"]})

    assert '"EQP009"' in js
    assert "window.FastView.selectDay(" in js


def test_build_fast_client_js_references_canvas_and_dom_ids():
    js = _build()

    for expected_id in (GANTT_CANVAS_ID, WIP_CANVAS_ID, TOOLTIP_ID, STAGE4_BODY_ID):
        assert f'getElementById("{expected_id}")' in js


def test_build_fast_client_js_single_file_mode_skips_fetch_for_other_days():
    js = _build(single_file=True)

    assert "var SINGLE_FILE = true;" in js
    assert "showUnavailableNotice" in js


def test_build_fast_client_js_does_not_reference_daily_chart_div_id_unused_yet():
    # ⑥-2側のPlotlyクリックはvisualize.py側で配線するため、
    # fast_client.py自体はこのdiv idを直接は使わない（定数として公開のみ）。
    assert DAILY_CHART_DIV_ID == "stage2-daily-chart"


def test_build_fast_client_js_references_axis_id():
    js = _build()

    assert f'getElementById("{AXIS_ID}")' in js


def test_build_fast_client_js_wires_wheel_zoom_and_drag_pan():
    js = _build()

    assert 'addEventListener("wheel"' in js
    assert 'addEventListener("mousedown"' in js
    assert 'addEventListener("mouseup"' in js
    assert "zoomAt(" in js
    assert "MIN_WINDOW_MIN" in js
    assert "MAX_WINDOW_MIN" in js


def test_build_fast_client_js_wires_double_click_reset():
    js = _build()

    assert 'addEventListener("dblclick"' in js
    assert "setView(0, DAY_MIN)" in js


def test_build_fast_client_js_resets_view_on_day_switch():
    js = _build()

    # applyPayload()内でズーム・パン状態をリセットしていること
    assert "function applyPayload(payload) {" in js
    apply_payload_body = js.split("function applyPayload(payload) {", 1)[1]
    apply_payload_body = apply_payload_body.split("\n  }", 1)[0]
    assert "setView(0, DAY_MIN)" in apply_payload_body


def test_build_fast_client_js_click_after_pan_does_not_select_lot():
    js = _build()

    # ドラッグでパンした直後のclickではdidPanガードでロット選択を行わない
    assert (
        'addEventListener("click", function (evt) {\n    if (didPan) { return; }' in js
    )


def _function_body(js, start_marker, end_marker):
    body = js.split(start_marker, 1)[1]
    return body.split(end_marker, 1)[0]


def test_build_fast_client_js_syncs_wip_chart_with_zoom():
    js = _build()

    zoom_at_body = _function_body(js, "function zoomAt(cursorMin, factor) {", "\n  }")
    assert "renderWip(currentPayload)" in zoom_at_body


def test_build_fast_client_js_syncs_wip_chart_with_pan():
    js = _build()

    pan_body = _function_body(
        js, 'window.addEventListener("mousemove", function (evt) {', "\n  });"
    )
    assert "renderWip(currentPayload)" in pan_body


def test_build_fast_client_js_syncs_wip_chart_with_double_click_reset():
    js = _build()

    dblclick_body = _function_body(
        js, 'addEventListener("dblclick", function () {', "\n  });"
    )
    assert "renderWip(currentPayload)" in dblclick_body


def test_build_fast_client_js_wip_x_axis_follows_view_window_not_fixed_day():
    js = _build()

    render_wip_body = _function_body(js, "function renderWip(payload) {", "\n  }")
    assert "wip.t_min[i] / 1440" not in render_wip_body
    assert "(wip.t_min[i] - viewStart) / viewWidth" in render_wip_body


def test_build_fast_client_js_embeds_eqp_status_colors():
    js = _build(color_status_processing="#dceefb", color_status_waiting="#eef0f2")

    assert '"#dceefb"' in js
    assert '"#eef0f2"' in js
    assert "STATUS_PROCESSING_BG" in js
    assert "STATUS_WAITING_BG" in js


def test_build_fast_client_js_eqp_status_background_drawn_before_segment_bars():
    js = _build()

    # 装置ステータス背景（稼働中/待機中）は区間バーより前に描画し、
    # バーが背景の上に乗るようにする（視認性を保つ）。
    render_gantt_body = _function_body(js, "function renderGantt(payload) {", "\n  }")
    status_bg_index = render_gantt_body.index("STATUS_WAITING_BG")
    segment_bar_index = render_gantt_body.index("isBusy ? COLOR_BUSY : COLOR_WAIT")
    assert status_bg_index < segment_bar_index


def test_build_fast_client_js_merges_overlapping_intervals_for_eqp_status():
    js = _build()

    assert "function mergeIntervals(pairs)" in js
    render_gantt_body = _function_body(js, "function renderGantt(payload) {", "\n  }")
    assert "mergeIntervals(" in render_gantt_body


def test_build_fast_client_js_references_wip_axis_id_and_renders_labels():
    js = _build()

    assert f'getElementById("{WIP_AXIS_ID}")' in js
    assert "function renderWipAxisLabels(maxTotal)" in js
    render_wip_body = _function_body(js, "function renderWip(payload) {", "\n  }")
    assert "renderWipAxisLabels(" in render_wip_body
