from datetime import datetime
from pathlib import Path

from analyse_tool.common.output_index import register_output


def test_register_output_creates_index_with_one_row(tmp_path: Path):
    output_dir = tmp_path / "trial_factory"
    output_path = output_dir / "20260830" / "report_120000.html"
    output_path.parent.mkdir(parents=True)
    output_path.write_text("<html></html>", encoding="utf-8")

    register_output(
        output_dir,
        tool_name="eqp_workload_analysis",
        output_path=output_path,
        note="4,211,253行",
        run_at=datetime(2026, 8, 30, 12, 0, 0),
    )

    html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert "eqp_workload_analysis" in html
    assert 'href="20260830/report_120000.html"' in html
    assert "4,211,253行" in html
    assert "2026-08-30 12:00:00" in html


def test_register_output_prepends_newest_row_first(tmp_path: Path):
    output_dir = tmp_path / "trial_factory"
    first = output_dir / "20260830" / "report_100000.html"
    second = output_dir / "20260830" / "report_110000.html"
    for p in (first, second):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("<html></html>", encoding="utf-8")

    register_output(output_dir, "t", first, run_at=datetime(2026, 8, 30, 10, 0, 0))
    register_output(output_dir, "t", second, run_at=datetime(2026, 8, 30, 11, 0, 0))

    html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert html.index("report_110000.html") < html.index("report_100000.html")


def test_register_output_escapes_note_text(tmp_path: Path):
    output_dir = tmp_path / "trial_factory"
    output_path = output_dir / "20260830" / "report.html"
    output_path.parent.mkdir(parents=True)
    output_path.write_text("<html></html>", encoding="utf-8")

    register_output(output_dir, "t", output_path, note="<script>alert(1)</script>")

    html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
