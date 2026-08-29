"""プロファイル（データ定義情報）から列データを生成するロジック本体。

各列は `ColumnProfile.role` に応じて別々の生成関数に振り分ける。
数百万〜数億行を想定し、numpy でベクトル化して生成する（1行ずつの
Pythonループはしない）。実際のチャンク分割・Parquet書き出しは `io.py` 側。
"""

from __future__ import annotations

import numpy as np
import pyarrow as pa

from analyse_tool.common.profile import ColumnProfile, DatasetProfile


def generate_table(profile: DatasetProfile, n: int, seed: int) -> pa.Table:
    """プロファイル全体から n 行ぶんの pyarrow Table を1つ作る。"""
    rng = np.random.default_rng(seed)
    arrays = {col.name: _generate_column(col, n, rng) for col in profile.columns}
    return pa.table(arrays)


def _generate_column(col: ColumnProfile, n: int, rng: np.random.Generator) -> pa.Array:
    if col.role == "id":
        values = _generate_id(col, n)
    elif col.role == "numeric":
        values = _generate_numeric(col, n, rng)
    elif col.role == "categorical":
        values = _generate_categorical(col, n, rng)
    elif col.role == "date":
        values = _generate_date(col, n, rng)
    elif col.role == "boolean":
        p = col.true_rate if col.true_rate is not None else 0.5
        values = rng.random(n) < p
    else:
        raise ValueError(f"未対応の role です: {col.role}（列: {col.name}）")

    if col.null_rate:
        mask = rng.random(n) < col.null_rate
        return pa.array(values, mask=mask)
    return pa.array(values)


def _generate_id(col: ColumnProfile, n: int) -> np.ndarray:
    seq = np.arange(1, n + 1, dtype=np.int64)
    if col.dtype == "string" and col.categories:
        prefix = col.categories[0].value
        return np.array([f"{prefix}{i:06d}" for i in seq], dtype=object)
    return seq


def _generate_numeric(col: ColumnProfile, n: int, rng: np.random.Generator) -> np.ndarray:
    if col.distribution == "normal":
        values = rng.normal(loc=col.mean or 0.0, scale=col.stddev or 1.0, size=n)
    elif col.distribution == "lognormal":
        values = rng.lognormal(mean=col.mean or 0.0, sigma=col.stddev or 1.0, size=n)
    else:  # uniform
        lo = col.min if col.min is not None else 0
        hi = col.max if col.max is not None else 1
        values = rng.uniform(lo, hi, size=n)

    if col.min is not None:
        values = np.maximum(values, col.min)
    if col.max is not None:
        values = np.minimum(values, col.max)
    if "int" in col.dtype:
        values = np.round(values).astype(np.int64)
    return values


def _generate_categorical(col: ColumnProfile, n: int, rng: np.random.Generator) -> np.ndarray:
    if not col.categories:
        raise ValueError(f"categorical列 '{col.name}' に categories がありません")
    values_list = [c.value for c in col.categories]
    freqs = np.array([c.freq for c in col.categories], dtype=float)
    freqs = freqs / freqs.sum()
    idx = rng.choice(len(values_list), size=n, p=freqs)
    return np.array(values_list, dtype=object)[idx]


def _generate_date(col: ColumnProfile, n: int, rng: np.random.Generator) -> np.ndarray:
    start = np.datetime64(col.min, "D")
    end = np.datetime64(col.max, "D")
    span = int((end - start) / np.timedelta64(1, "D"))
    offsets = rng.integers(0, span + 1, size=n)
    return start + offsets.astype("timedelta64[D]")
