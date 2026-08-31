import plotly.graph_objects as go

from analyse_tool.common.report import _dom_id, build_multi_stage_drilldown_html


def _bar_fig(x_values):
    fig = go.Figure(go.Bar(x=x_values, y=[1] * len(x_values)))
    return fig


def test_dom_id_replaces_non_alnum_characters():
    assert _dom_id("EQP-009") == "EQP-009"
    assert _dom_id("EQP 009/A") == "EQP_009_A"


def test_build_multi_stage_drilldown_html_embeds_all_stage_divs_and_data():
    html = build_multi_stage_drilldown_html(
        title="テストレポート",
        lead_sections_html=["<section>lead</section>"],
        stage1_fig=_bar_fig(["E1", "E2"]),
        stage1_heading="段1",
        stage2_figs={"E1": _bar_fig([1, 2]), "E2": _bar_fig([3, 4])},
        stage2_default_key="E1",
        stage2_heading="段2",
        stage3_default_fig=_bar_fig([0]),
        stage3_heading="段3",
        stage3_curve_number=0,
        stage4_heading="段4",
        lot_detail_columns=["lot_id", "eqp_id"],
        lot_detail_data={"lot_id": ["LOT001"], "eqp_id": ["E1"]},
        domain_js="window.EqpDrilldown = {onStage1Select: function(){}, onStage2Select: function(){}, onStage3Select: function(){}};",
    )

    assert "<!DOCTYPE html>" in html
    assert 'id="stage1-pareto"' in html
    assert 'id="stage2-E1"' in html
    assert 'id="stage2-E2"' in html
    assert 'id="stage3-chart"' in html
    assert 'id="stage4-body"' in html
    assert "テストレポート" in html
    assert "LOT001" in html
    assert "<section>lead</section>" in html


def test_build_multi_stage_drilldown_html_hides_non_default_stage2_figs():
    html = build_multi_stage_drilldown_html(
        title="t",
        lead_sections_html=[],
        stage1_fig=_bar_fig(["E1", "E2"]),
        stage1_heading="段1",
        stage2_figs={"E1": _bar_fig([1]), "E2": _bar_fig([2])},
        stage2_default_key="E2",
        stage2_heading="段2",
        stage3_default_fig=_bar_fig([0]),
        stage3_heading="段3",
        stage3_curve_number=0,
        stage4_heading="段4",
        lot_detail_columns=["lot_id"],
        lot_detail_data={"lot_id": []},
        domain_js="",
    )

    e1_start = html.index('data-key="E1"')
    e1_style_end = html.index(">", e1_start)
    assert "display:none" in html[e1_start:e1_style_end]

    e2_start = html.index('data-key="E2"')
    e2_style_end = html.index(">", e2_start)
    assert "display:block" in html[e2_start:e2_style_end]


def test_build_multi_stage_drilldown_html_escapes_disclaimer_text():
    html = build_multi_stage_drilldown_html(
        title="t",
        lead_sections_html=[],
        stage1_fig=_bar_fig(["E1"]),
        stage1_heading="段1",
        stage2_figs={"E1": _bar_fig([1])},
        stage2_default_key="E1",
        stage2_heading="段2",
        stage3_default_fig=_bar_fig([0]),
        stage3_heading="段3",
        stage3_curve_number=0,
        stage4_heading="段4",
        lot_detail_columns=["lot_id"],
        lot_detail_data={"lot_id": []},
        domain_js="",
        disclaimer="<script>x</script>",
    )

    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html


def test_existing_single_stage_api_is_unchanged():
    # 既存の1段版APIが壊れていないことを確認する（customer_pref_summary互換）。
    import pandas as pd

    from analyse_tool.common.report import build_bar_click_detail_html

    detail_df = pd.DataFrame(
        {"pref": ["東京"], "segment": ["個人"], "customer_id": ["C1"]}
    )
    html = build_bar_click_detail_html(
        _bar_fig(["東京"]),
        detail_df,
        detail_match_columns={"x": "pref", "trace_name": "segment"},
        title="既存レポート",
    )
    assert "既存レポート" in html
