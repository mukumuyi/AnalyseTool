# 技術仕様書

## テクノロジースタック

| 分類 | 採用技術 | 用途 |
| --- | --- | --- |
| 言語 | Python（`.python-version`で3.10系に固定） | 全ツール共通 |
| パッケージ管理 | uv（`pyproject.toml`/`uv.lock`） | 依存管理・実行 |
| データエンジン | DuckDB | 大規模データのSQLによる読み込み・フィルタ・結合・集計 |
| クエリ言語 | SQL（DuckDB上で実行） | `prepare`/`process`/`analyze`における加工・集計の主要手段 |
| データ形式 | Parquet | 入力データ・中間ファイルの標準形式 |
| データ処理（小規模） | pandas | 集計後の小さいデータの整形・可視化直前のデータ受け渡し |
| データ書き出し（生成） | pyarrow | `generate_sample_data`でnumpy配列から型を制御しつつParquetへチャンク単位で追記書き込み |
| データ生成 | numpy | サンプルデータ生成のベクトル化演算 |
| 可視化 | Plotly | 自己完結HTMLレポート（`fig.write_html()`） |
| 可視化（大量点） | WebGL（Plotlyの`scattergl`） | 散布図等で大量点でもインタラクティブに描画するための既定レンダラ |
| Lint/フォーマット | ruff | コーディング規約の自動チェック・整形 |
| 型チェック | mypy | 静的型チェック |
| テスト | pytest | ユニットテスト |

## 主要な技術選定の判断根拠

### DuckDB + Parquetを大規模データ処理の標準にする

`prepare.py`/`process.py`はDuckDB（SQL）を第一選択にし、pandasには集計済み・
絞り込み済みの小さいデータだけを渡す。

**判断理由**: `ER_DuckDB`という別プロジェクトでの実測で、同一の集計処理を
DuckDB+Parquetとpandas+CSVで比較したところ、DuckDB側が数百〜千倍高速だった。
数百万〜数億行という想定データ量では、全件をpandasのDataFrameへロードして
から加工する方式は現実的でない。

### WebGL（Plotly `scattergl`）を大量データ描画の既定にする

大量データのインタラクティブ描画にはPlotlyのWebGL（`scattergl`）を既定とし、
**DuckDB-Wasm + Canvas（ブラウザ側でDuckDBを実行し、生データに都度SQLを
投げる方式）は今は採用しない**。将来ニーズが変わったときの拡張候補として
判断根拠を残す。

| | WebGL（`scattergl`）採用 | DuckDB-Wasm + Canvas（不採用） |
| --- | --- | --- |
| 重い処理の場所 | Python側（DuckDB）で集計済みデータをHTMLに埋め込み、ブラウザは描画のみ | ブラウザ側でDuckDBを実行し、生Parquetに都度SQLを実行 |
| できること | パン・ズーム・ホバー・凡例トグルなど「見せ方の操作」 | グルーピング変更・再集計などの「問い直し（再クエリ）」 |
| 配布 | 自己完結HTML1枚、`file://`でそのまま開ける | wasm/JS/Parquet一式が必要。`file://`だとfetchがCORSでブロックされがちで簡易サーバーが要ることが多い |
| 実装コスト | `fig.write_html()`で完結。既存のPythonスタックのまま | JS/WASMのグルーコードを自前実装。技術スタックが増える |

**判断理由**: 本プロジェクトは「`analyze.py`で可視化用に集計・サンプリング
してから`visualize.py`に渡す」設計を前提にしている。この前提では、ブラウザ
は軽量化済みデータをきれいに描画できればよく、`scattergl`で十分。
DuckDB-Wasmが活きるのは「事前集計をせず生データに対してブラウザ側でその場
でクエリを投げ直したい」という、今とは異なるユースケース（ミニBIツールに
近いもの）で、実装・配布の手間も一段重くなる。

**再検討する条件**: 「スクリプトを再実行せず、レポートを開いたままフィルタ
条件を変えて何度も掘り下げたい」というニーズが強くなったら、
DuckDB-Wasm+Canvasへの切り替えを検討する。

## 開発ツールと手法

- 実行: `uv run python scripts/<スクリプト名>.py [オプション]`
- 依存追加: `uv add <パッケージ名>`（開発専用は`uv add --dev <パッケージ名>`）
- Lint/フォーマット: `uv run ruff check .` / `uv run ruff format .`
- 型チェック: `uv run mypy .`
- テスト実行: `uv run pytest`
- Git運用: GitFlowに従う（詳細は`docs/development-guidelines.md`のGit規約）
- ドキュメント運用: 永続的ドキュメント（`docs/`）と作業単位ドキュメント
  （`.steering/`）の使い分けは`CLAUDE.md`を参照

## 設計原則

- **モジュール化**: 各ツールは`prepare`/`process`/`analyze`/`visualize`の
  4ステップ（例外的なツールは`cli.py`/`io.py`+処理本体）に分割し、
  1モジュール・1関数の責務を絞る。
- **関心の分離**: データ加工（DuckDBのSQL）と可視化（Plotly）を分離する。
  4ステップの各関数はファイルI/Oを直接行わず、`io.py`経由でデータを
  やり取りする。
- **再利用性**: 複数ツールで共通する処理は`src/analyse_tool/common/`に
  切り出し、各ツールのサブパッケージから読み込む。
- **依存の方向**: `common/`配下は各ツールのサブパッケージに依存しない
  一方向の関係を保つ。ツール間（例:`customer_pref_summary`と
  `generate_sample_data`）の相互依存も禁止する。

具体的なモジュール分割・依存関係の設計は`docs/functional-design.md`の
「コンポーネント設計」に記載し、フォルダ構成への反映は
`docs/repository-structure.md`に記載する。

## 技術的制約と要件

- **実行環境**: ローカルPCでの単一ユーザー実行を前提とし、サーバーの
  常時稼働は行わない。
- **Pythonバージョン**: `.python-version`（現在`3.10`）、
  `pyproject.toml`の`requires-python = ">=3.10"`に準拠する。
- **ブラウザ**: 可視化レポートは`file://`で直接開けるモダンブラウザ
  （Chrome/Edge/Firefox等）を前提とし、WebGL（`scattergl`）が有効で
  あることを前提とする。
- **パッケージング**: `src/analyse_tool/__init__.py`が存在しない間は
  `pyproject.toml`の`[tool.uv] package = false`により、自身を
  ビルド対象パッケージとして扱わない。`src/`を本採用したらこの設定を
  見直す。
- **将来のdbt導入を見据えたSQLの書き方**: `process.py`/`analyze.py`内の
  DuckDB SQLは、1関数=1つの完結したSELECT文とし、文字列結合による
  動的SQL組み立て（条件によってSQL文自体を分岐生成する等）は避ける。
  これにより、将来`dbt`のmodelへ機械的に移行しやすくする（具体的な
  移行手順・対応表は導入時に作成する）。
- **ロギング**: 現状は`print()`による標準出力のみを方針とする。ログ
  レベル管理等が必要になった場合は`logging`モジュールへの移行を検討する
  （詳細な規約は`docs/development-guidelines.md`で定める）。
- **依存バージョン・DuckDB互換性**: `uv.lock`はコミットして固定し、依存の
  更新は`uv add`/`uv sync`経由で行う。特にDuckDBはバージョン間でSQL挙動
  が変わりうるため、バージョンを上げる際は主要ツールの動作確認をしてから
  `uv.lock`を更新する。
- **エラーハンドリング・出力の安全性**: 出力ファイルは既存ファイルを
  上書きする方針だが、大量データ生成中の異常終了で壊れた（中途半端な）
  ファイルが残るリスクがある。安全な書き込み（一時ファイルへ書いてから
  成功時のみリネームする等）の具体的な規約は`docs/development-guidelines.md`
  で定める。

## パフォーマンス要件

- 数百万〜数億行規模のデータでも、`prepare`/`process`がpandasへ全件
  ロードせず、DuckDBのSQL集計で完結すること。
- `generate_sample_data`は`CHUNK_ROWS`（既定100万行）単位でParquetを
  追記書き出しし、メモリ使用量を一定に保つ。
- 大量点が必要な散布図は`scattergl`（WebGL）を既定にし、描画点数が
  数万点程度を超える場合は間引き・ビニング集計を検討する。
- 複数グラフを1つのHTMLにまとめる際は`include_plotlyjs="cdn"`を使い、
  plotly.js本体を毎回埋め込まない。
