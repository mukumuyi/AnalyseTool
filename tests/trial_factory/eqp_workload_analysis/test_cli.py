from analyse_tool.trial_factory.eqp_workload_analysis.cli import parse_args


def test_parse_args_defaults():
    args = parse_args([])

    assert args.input == "data/trial_factory/proc_history.parquet"
    assert args.output_dir == "output"
    assert args.top_n == 15
    assert args.period_days == 3
    assert args.gantt_window_hours == 4


def test_parse_args_overrides():
    args = parse_args(
        [
            "--input",
            "custom.parquet",
            "--output-dir",
            "out2",
            "--top-n",
            "5",
            "--period-days",
            "1",
            "--gantt-window-hours",
            "2",
        ]
    )

    assert args.input == "custom.parquet"
    assert args.output_dir == "out2"
    assert args.top_n == 5
    assert args.period_days == 1
    assert args.gantt_window_hours == 2
