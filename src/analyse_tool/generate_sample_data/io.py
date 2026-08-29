"""プロファイル(JSON)の読み込みと、生成データのParquet書き出し。"""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq

from analyse_tool.common.profile import DatasetProfile, load_profile

from .generate import generate_table

CHUNK_ROWS = 1_000_000
"""1回に生成する行数。数億行でも一度にメモリへ載せないためのチャンクサイズ。"""


def read_profile(path: str | Path) -> DatasetProfile:
    """データ定義情報（プロファイル）のJSONを読み込む。"""
    return load_profile(path)


def write_parquet(profile: DatasetProfile, n: int, seed: int, output_path: str | Path) -> None:
    """n行ぶんのサンプルデータを生成し、Parquetへ書き出す。

    `CHUNK_ROWS` 行ずつ生成してそのつど書き出すことで、n が数億行でも
    メモリ使用量を一定に抑える。
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    writer: pq.ParquetWriter | None = None
    remaining = n
    chunk_index = 0
    try:
        while remaining > 0:
            rows = min(CHUNK_ROWS, remaining)
            table = generate_table(profile, rows, seed=seed + chunk_index)
            if writer is None:
                writer = pq.ParquetWriter(output_path, table.schema)
            writer.write_table(table)
            remaining -= rows
            chunk_index += 1
    finally:
        if writer is not None:
            writer.close()
