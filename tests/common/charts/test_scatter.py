import pandas as pd

from analyse_tool.common.charts.scatter import scatter


def test_scatter_uses_scattergl_and_markers_mode():
    df = pd.DataFrame(
        {"count": [10, 20], "wait_avg": [5.0, 12.0], "eqp_id": ["E1", "E2"]}
    )

    fig = scatter(df, x="count", y="wait_avg", text="eqp_id")

    assert len(fig.data) == 1
    trace = fig.data[0]
    assert trace.type == "scattergl"
    assert trace.mode == "markers"
    assert list(trace.text) == ["E1", "E2"]
