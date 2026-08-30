"""`docs/reference/` 配下をpytestから実行するためのパス設定。

`analyse_tool` パッケージは本採用前のため `src/` には無く、この
`docs/reference/` 直下に置かれている。テストから `import analyse_tool...`
できるよう、このディレクトリをsys.pathへ追加する。

実行方法:
    uv run pytest docs/reference/tests
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
