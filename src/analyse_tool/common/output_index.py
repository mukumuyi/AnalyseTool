"""`output/<プロジェクト名>/index.html`（生成物の目次）を更新する共通処理。

各ツールの`io.py`が個別に目次のHTMLを組み立てるのではなく、レポート等を
書き出した後にここの`register_output()`を呼ぶだけで済むようにする
（`docs/repository-structure.md`の「`output/`の構成」を参照）。

`file://`で開いてそのままブラウザ遷移できるよう、自己完結HTMLとして
`output/<プロジェクト名>/index.html`に1行ずつ追記する。
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path

_ROW_MARKER = "<!-- rows -->"

_EMPTY_TEMPLATE = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>出力一覧</title>
<style>
  body {{ font-family: -apple-system, "Hiragino Sans", "Yu Gothic", sans-serif; margin: 24px; }}
  h1 {{ font-size: 1.3em; }}
  table {{ border-collapse: collapse; font-size: 0.9em; }}
  th, td {{ border: 1px solid #ddd; padding: 4px 10px; text-align: left; }}
  th {{ background: #f4f4f4; }}
</style>
</head>
<body>
<h1>出力一覧</h1>
<table>
  <thead><tr><th>実行日時</th><th>ツール</th><th>生成物</th><th>備考</th></tr></thead>
  <tbody>
    {_ROW_MARKER}
  </tbody>
</table>
</body>
</html>
"""


def register_output(
    project_output_dir: str | Path,
    tool_name: str,
    output_path: str | Path,
    note: str = "",
    run_at: datetime | None = None,
) -> None:
    """`<project_output_dir>/index.html`の目次テーブルの先頭に1行追加する。

    Args:
        project_output_dir: `output/<プロジェクト名>/`のパス。
        tool_name: 生成物を作ったツール名。
        output_path: 生成物へのパス。`project_output_dir`からの相対パスに
            変換してリンクする。
        note: 備考（件数・絞り込み条件等、任意）。
        run_at: 実行日時。省略時は現在時刻。
    """
    project_output_dir = Path(project_output_dir)
    project_output_dir.mkdir(parents=True, exist_ok=True)
    index_path = project_output_dir / "index.html"
    run_at = run_at or datetime.now()

    html = (
        index_path.read_text(encoding="utf-8")
        if index_path.exists()
        else _EMPTY_TEMPLATE
    )

    relative_path = (
        Path(output_path).resolve().relative_to(project_output_dir.resolve())
    )
    row = (
        f"<tr><td>{run_at:%Y-%m-%d %H:%M:%S}</td><td>{_escape(tool_name)}</td>"
        f'<td><a href="{relative_path.as_posix()}">{_escape(relative_path.name)}</a></td>'
        f"<td>{_escape(note)}</td></tr>"
    )
    updated_html = html.replace(_ROW_MARKER, f"{_ROW_MARKER}\n      {row}", 1)

    _write_atomically(index_path, updated_html)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _write_atomically(path: Path, content: str) -> None:
    """一時ファイルに書いてから`os.replace()`でリネームする（安全な書き込み）。"""
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except BaseException:
        Path(tmp_path).unlink(missing_ok=True)
        raise
