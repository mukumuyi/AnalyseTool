#!/usr/bin/env python
"""エントリポイント。実処理は src/analyse_tool/customer_pref_summary/ を参照。

使い方:
    uv run python scripts/customer_pref_summary.py \\
        --input output/customers_sample.parquet --output output/customer_pref_summary.html
"""

from analyse_tool.customer_pref_summary import main

if __name__ == "__main__":
    main()
