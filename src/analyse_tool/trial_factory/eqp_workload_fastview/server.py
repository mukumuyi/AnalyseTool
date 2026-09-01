"""高速モード — 生成済み出力ディレクトリを配信するローカル静的サーバー。

追加の依存を増やさないよう、標準ライブラリの`http.server`だけで実装する
（`.steering/20260901-eqp-workload-fastview/design.md`の「課題対応」
参照。`eqp_workload_fastview`のみで使うため`common/`へは切り出さない）。
生成済みのデータを配信するだけで、サーバー側での再集計は行わない
（`--serve`前に必ずレポート生成が完了している前提）。
"""

from __future__ import annotations

import functools
import http.server
from pathlib import Path


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """アクセスログを標準エラー出力へ流さないハンドラ。"""

    def log_message(self, format: str, *args: object) -> None:
        pass


def build_server(
    directory: str | Path, port: int = 0
) -> http.server.ThreadingHTTPServer:
    """`directory`直下の`index.html`を配信するサーバーを作る（まだ待ち受けはしない）。

    Args:
        directory: レポート生成済みの出力ディレクトリ（`index.html`を含む）。
        port: 待ち受けポート。`0`はOSに空きポートを自動選択させる。

    Raises:
        FileNotFoundError: `directory`に`index.html`が無い場合
            （レポート未生成であることを示すため、起動前に分かりやすく
            エラーにする）。
    """
    directory = Path(directory)
    if not (directory / "index.html").exists():
        raise FileNotFoundError(
            f"{directory} に index.html が見つかりません。"
            "先にレポート生成（--serveを付けずに実行）を行ってください。"
        )
    handler = functools.partial(_QuietHandler, directory=str(directory))
    return http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)


def server_url(server: http.server.ThreadingHTTPServer) -> str:
    """サーバーの`index.html`へのURLを返す。"""
    _, port = server.server_address[:2]
    return f"http://127.0.0.1:{port}/index.html"


def serve(directory: str | Path, port: int = 0) -> None:
    """`directory`を配信し、URLを標準出力へ表示してCtrl+Cまで待ち受ける。"""
    server = build_server(directory, port)
    print(f"起動しました: {server_url(server)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
