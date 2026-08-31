#!/usr/bin/env python
"""エントリポイント。実処理は src/analyse_tool/trial_factory/eqp_workload_analysis/ を参照。

使い方:
    uv run python scripts/trial_factory/eqp_workload_analysis.py \\
        --input data/trial_factory/proc_history.parquet --output-dir output
"""

from analyse_tool.trial_factory.eqp_workload_analysis import main

if __name__ == "__main__":
    main()
