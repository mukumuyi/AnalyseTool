"""generate_proc_history: proc_history（工程実績履歴）のサンプルデータを作るツール。

`python -m generate_proc_history`から呼ばれるエントリポイント。このツールは
分析ツールではなくユーティリティのため、前準備/データ加工/分析/可視化の
4ステップ構成ではなく、`cli.py`（引数）/`config.py`（設定フォーマット）/
`io.py`（読み書き）/`generate.py`（生成ロジック）/`validate.py`（生成結果の
検証）というモジュール構成にしている。
"""

from __future__ import annotations

from .cli import parse_args
from .generate import generate_table
from .io import read_config, write_parquet
from .validate import validate_table


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config = read_config(args.config)
    if args.lot_count is not None:
        config.lot_count = args.lot_count

    table = generate_table(config, seed=args.seed)

    violations = validate_table(table)
    if violations:
        print("生成結果が生成ルールを満たしていません。Parquetは書き出しません。")
        for v in violations:
            print(f"- {v}")
        raise SystemExit(1)

    write_parquet(table, args.output)
    print(f"生成完了: {args.output} ({table.num_rows:,}行, config={config.name})")
