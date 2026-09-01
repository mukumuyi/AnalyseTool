import threading
import urllib.request
from pathlib import Path

import pytest

from analyse_tool.trial_factory.eqp_workload_fastview.server import (
    build_server,
    server_url,
)


def test_build_server_raises_when_index_html_is_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        build_server(tmp_path)


def test_serve_serves_index_html_over_http(tmp_path: Path):
    (tmp_path / "index.html").write_text("<html>fastview</html>", encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "daily_index.json").write_text("{}", encoding="utf-8")

    server = build_server(tmp_path, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = server_url(server)
        assert url.endswith("/index.html")
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read().decode("utf-8")
        assert body == "<html>fastview</html>"

        with urllib.request.urlopen(
            url.replace("index.html", "data/daily_index.json"), timeout=5
        ) as response:
            assert response.read().decode("utf-8") == "{}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
