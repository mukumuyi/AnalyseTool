#!/usr/bin/env python
"""エントリポイント。実処理は src/analyse_tool/generate_sample_data/ を参照。

使い方:
    uv run python scripts/generate_sample_data.py \\
        --profile profiles/orders.json --output output/orders_sample.parquet
"""

from analyse_tool.generate_sample_data import main

if __name__ == "__main__":
    main()
