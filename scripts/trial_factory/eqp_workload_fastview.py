#!/usr/bin/env python
"""エントリポイント。実処理は src/analyse_tool/trial_factory/eqp_workload_fastview/ を参照。

使い方:
    uv run python scripts/trial_factory/eqp_workload_fastview.py \\
        --input data/trial_factory/proc_history.parquet --output-dir output --serve
"""

from analyse_tool.trial_factory.eqp_workload_fastview import main

if __name__ == "__main__":
    main()
