"""設定(JSON)の読み込みと、生成データのParquet書き出し。"""

from __future__ import annotations

import os
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from .config import ProcHistoryConfig, load_config


def read_config(path: str | Path) -> ProcHistoryConfig:
    """proc_history生成用の設定JSONを読み込む。"""
    return load_config(path)


def write_parquet(table: pa.Table, output_path: str | Path) -> None:
    """生成済みの`pyarrow.Table`をParquetへ書き出す。

    `docs/development-guidelines.md`の「出力ファイルの安全な書き込み」に
    従い、同じディレクトリの一時ファイルに書いてから、成功した場合のみ
    `os.replace()`でリネームする。書き込み中に異常終了しても、壊れた
    （中途半端な）ファイルが出力先に残らないようにするため。
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        pq.write_table(table, tmp_path)
        os.replace(tmp_path, output_path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
