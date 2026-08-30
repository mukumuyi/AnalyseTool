"""generate_sample_data: データ定義情報（プロファイル）からサンプルデータを作るツール。

`scripts/generate_sample_data.py` から呼ばれるエントリポイント。
このツールは分析ツールではなくユーティリティのため、
前準備/データ加工/分析/可視化の4ステップ構成ではなく、
`cli.py`（引数） / `io.py`（読み書き） / `generate.py`（生成ロジック）
の3モジュール構成にしている。
"""

from __future__ import annotations

from .cli import parse_args
from .io import read_profile, write_parquet


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    profile = read_profile(args.profile)
    rows = args.rows if args.rows is not None else profile.row_count
    write_parquet(profile, n=rows, seed=args.seed, output_path=args.output)
    print(f"生成完了: {args.output} ({rows:,}行, profile={profile.name})")
