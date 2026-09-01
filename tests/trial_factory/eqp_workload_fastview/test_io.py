import json
from pathlib import Path

from analyse_tool.trial_factory.eqp_workload_fastview.io import write_fastview_report


def test_write_fastview_report_writes_shell_index_and_day_files(tmp_path: Path):
    project_output_dir = tmp_path / "trial_factory"
    output_dir = project_output_dir / "20260901" / "eqp_workload_fastview_120000"

    index_path = write_fastview_report(
        output_dir=str(output_dir),
        shell_html="<html>shell</html>",
        daily_index_payload={"days": ["2026-01-01"], "utilization_pct": [12.5]},
        day_payloads={
            "2026-01-01": {"date": "2026-01-01", "segments": {}},
            "2026-01-02": {"date": "2026-01-02", "segments": {}},
        },
        project_output_dir=str(project_output_dir),
        note="test note",
    )

    assert index_path == output_dir / "index.html"
    assert index_path.read_text(encoding="utf-8") == "<html>shell</html>"

    daily_index = json.loads(
        (output_dir / "data" / "daily_index.json").read_text(encoding="utf-8")
    )
    assert daily_index["days"] == ["2026-01-01"]

    day1 = json.loads(
        (output_dir / "data" / "days" / "2026-01-01.json").read_text(encoding="utf-8")
    )
    assert day1["date"] == "2026-01-01"
    assert (output_dir / "data" / "days" / "2026-01-02.json").exists()

    index_html = (project_output_dir / "index.html").read_text(encoding="utf-8")
    assert "eqp_workload_fastview" in index_html
    assert "test note" in index_html


def test_write_fastview_report_overwrites_cleanly_on_rerun(tmp_path: Path):
    project_output_dir = tmp_path / "trial_factory"
    output_dir = project_output_dir / "20260901" / "eqp_workload_fastview_120000"

    write_fastview_report(
        output_dir=str(output_dir),
        shell_html="<html>first</html>",
        daily_index_payload={},
        day_payloads={},
        project_output_dir=str(project_output_dir),
    )
    write_fastview_report(
        output_dir=str(output_dir),
        shell_html="<html>second</html>",
        daily_index_payload={},
        day_payloads={},
        project_output_dir=str(project_output_dir),
    )

    assert (output_dir / "index.html").read_text(
        encoding="utf-8"
    ) == "<html>second</html>"
    # 一時ファイルが残っていないこと
    assert list(output_dir.glob(".*.tmp")) == []
