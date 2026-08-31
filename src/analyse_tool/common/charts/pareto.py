"""パレート図を組み立てる共通モジュール（第2層＝分析の型）。

「値の多い順に並べ、累積構成比を折れ線で重ねる」というパレート図の
分析パターンを、ドメイン知識なしに提供する。並べ替え・累積構成比の
算出は純粋関数として切り出し、実際の描画（棒＋第2軸の折れ線）は
第1層の`barline.py`に委譲する（同じ「棒＋第2軸の折れ線」という見た目を
装置稼働グラフ等と重複実装しないため）。
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from analyse_tool.common.charts.barline import bar_with_line

RANK_COLUMN = "rank"
CUM_PCT_COLUMN = "cum_pct"


def pareto_data(
    df: pd.DataFrame, category: str, value: str, top_n: int | None = None
) -> pd.DataFrame:
    """`value`の降順に並べ替え、順位（`rank`）と累積構成比（`cum_pct`）を付与する。

    Args:
        df: `category`ごとの集計値を持つデータ（1カテゴリ1行）。
        category: カテゴリの列名（例: `eqp_id`）。
        value: 並べ替え・構成比の基準にする値の列名（例: 待機時間合計）。
        top_n: 上位何件を残すか。省略時は全件。累積構成比は
            **絞り込み前の全体**に対する割合として計算する（上位N件だけで
            構成比が100%に達したように見えるのを防ぐ）。

    Returns:
        `category`/`value`列に加え、`rank`（1始まりの順位）・`cum_pct`
        （0.0〜1.0の累積構成比）を付与し、`value`降順に並べたデータ。
    """
    sorted_df = df.sort_values(value, ascending=False, kind="stable").reset_index(
        drop=True
    )
    total = sorted_df[value].sum()
    sorted_df[RANK_COLUMN] = sorted_df.index + 1
    sorted_df[CUM_PCT_COLUMN] = sorted_df[value].cumsum() / total if total else 0.0

    if top_n is not None:
        sorted_df = sorted_df.head(top_n).reset_index(drop=True)
    return sorted_df


def pareto_chart(
    df: pd.DataFrame,
    category: str,
    value: str,
    cum_pct: str = CUM_PCT_COLUMN,
    threshold: float | None = 0.8,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """パレート図（棒＋累積構成比の折れ線）を作る。

    Args:
        df: `pareto_data()`が返す形式のデータ（`value`降順に並んでいる前提）。
        category: 横軸の列名。
        value: 棒（主軸）の値の列名。
        cum_pct: 累積構成比（第2軸の折れ線）の列名。
        threshold: 目安線を引く累積構成比（例: 0.8＝80%線）。`None`で非表示。
        title, x_title, y_title: グラフ・軸のタイトル。

    Returns:
        `barline.bar_with_line()`が返す`go.Figure`に、`threshold`指定時は
        80%目安線などの水平線を追加したもの。
    """
    x_order = list(df[category])
    fig = bar_with_line(
        df,
        x=category,
        y_bar=value,
        y_line=cum_pct,
        x_order=x_order,
        title=title,
        x_title=x_title,
        y_bar_title=y_title,
        y_line_title="累積構成比",
        line_name="累積構成比",
    )
    if threshold is not None:
        fig.add_hline(
            y=threshold,
            yref="y2",
            line={"color": "gray", "dash": "dash"},
            annotation_text=f"{threshold:.0%}",
        )
    return fig
