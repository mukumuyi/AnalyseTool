"""proc_history生成専用の設定フォーマット（`ProcHistoryConfig`）。

`proc_history`は品目階層（`prodspec_id`→`mainpd_id`）・ルーティング
（`ope_no`×`ope_seq`）・設備ごとに固定の処理時間・ロット内での時系列の
単調増加、という行間・列間の依存関係を持つ。`common/profile.py`の
`DatasetProfile`（列ごとに独立して値を生成する前提）ではこれを表現
できないため、このツール専用の別形式として定義する。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal


@dataclass
class MinMax:
    """整数の範囲（両端を含む）。"""

    min: int
    max: int


@dataclass
class LognormalSpec:
    """対数正規分布のパラメータ。

    `mean`/`stddev`は`common/profile.py`の`lognormal`と同じく、対数正規
    分布の元になる正規分布側のパラメータ（実際の値の平均・標準偏差では
    ない）。`min`/`max`で生成後の値をクリップする。
    """

    distribution: Literal["lognormal"]
    mean: float
    stddev: float
    min: float
    max: float


@dataclass
class TimeRange:
    """データ全体の対象期間（ISO 8601形式の日時文字列）。"""

    start: str
    end: str


@dataclass
class ProcHistoryConfig:
    """`proc_history`生成用の設定一式。"""

    name: str
    prodspec_count: int
    mainpd_per_prodspec: MinMax
    ope_name_pool: list[str]
    steps_per_routing: MinMax
    eqp_count: int
    eqp_per_ope_name: MinMax
    eqp_processing_minutes: LognormalSpec
    queue_minutes: LognormalSpec
    lot_count: int
    time_range: TimeRange

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> ProcHistoryConfig:
        d = dict(d)
        d["mainpd_per_prodspec"] = MinMax(**d["mainpd_per_prodspec"])
        d["steps_per_routing"] = MinMax(**d["steps_per_routing"])
        d["eqp_per_ope_name"] = MinMax(**d["eqp_per_ope_name"])
        d["eqp_processing_minutes"] = LognormalSpec(**d["eqp_processing_minutes"])
        d["queue_minutes"] = LognormalSpec(**d["queue_minutes"])
        d["time_range"] = TimeRange(**d["time_range"])
        return ProcHistoryConfig(**d)


def load_config(path: str | Path) -> ProcHistoryConfig:
    """設定JSONファイルを読み込む。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ProcHistoryConfig.from_dict(data)
