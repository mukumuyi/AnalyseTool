from pathlib import Path

from analyse_tool.trial_factory.eqp_workload_analysis.io import write_report_html


def test_write_report_html_writes_file_and_registers_output(tmp_path: Path):
    output_dir = tmp_path / "trial_factory"
    report_path = output_dir / "20260830" / "eqp_workload_analysis_120000.html"

    write_report_html(
        "<html>report</html>",
        str(report_path),
        project_output_dir=str(output_dir),
        note="test note",
    )

    assert report_path.read_text(encoding="utf-8") == "<html>report</html>"
    index_html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert "eqp_workload_analysis_120000.html" in index_html
    assert "test note" in index_html
