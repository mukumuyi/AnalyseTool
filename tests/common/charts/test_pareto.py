import pandas as pd

from analyse_tool.common.charts.pareto import pareto_chart, pareto_data


def test_pareto_data_sorts_descending_and_computes_cumulative_pct():
    df = pd.DataFrame({"eqp_id": ["E3", "E1", "E2"], "wait_total": [30, 100, 70]})

    result = pareto_data(df, category="eqp_id", value="wait_total")

    assert list(result["eqp_id"]) == ["E1", "E2", "E3"]
    assert list(result["rank"]) == [1, 2, 3]
    assert result["cum_pct"].iloc[-1] == 1.0  # 全件を含めれば必ず100%に収束する
    assert list(result["cum_pct"].round(2)) == [0.5, 0.85, 1.0]


def test_pareto_data_top_n_keeps_cumulative_pct_relative_to_the_full_total():
    df = pd.DataFrame({"eqp_id": ["E1", "E2", "E3"], "wait_total": [100, 70, 30]})

    result = pareto_data(df, category="eqp_id", value="wait_total", top_n=2)

    assert len(result) == 2
    # 上位2件だけの合計(170)に対してではなく、全体(200)に対する割合であること
    assert result["cum_pct"].iloc[-1] == 0.85


def test_pareto_data_handles_zero_total_without_dividing_by_zero():
    df = pd.DataFrame({"eqp_id": ["E1", "E2"], "wait_total": [0, 0]})

    result = pareto_data(df, category="eqp_id", value="wait_total")

    assert list(result["cum_pct"]) == [0.0, 0.0]


def test_pareto_chart_delegates_to_barline_and_adds_threshold_line():
    df = pareto_data(
        pd.DataFrame({"eqp_id": ["E1", "E2"], "wait_total": [100, 50]}),
        category="eqp_id",
        value="wait_total",
    )

    fig = pareto_chart(df, category="eqp_id", value="wait_total", threshold=0.8)

    assert [trace.type for trace in fig.data] == ["bar", "scatter"]
    assert len(fig.layout.shapes) == 1
    assert fig.layout.shapes[0].y0 == 0.8
