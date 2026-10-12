# AnalyseTool

DATA分析で使うツールスクリプトを溜めていく社内ツール集。目的・背景は
[docs/product-requirements.md](docs/product-requirements.md)を参照。

## セットアップ

クローン後に次を実行する。Pythonのバージョンは`.python-version`に準拠する。

```bash
uv sync                              # 依存をインストール（uvが必要）
uv run pytest                        # 動作確認（任意）
```


品質チェック（ruff・mypy・pytest）を含む詳細は
[docs/development-process.md](docs/development-process.md)の
「環境セットアップの内容」を参照。


## 使い方（本採用後）

本採用後の各ツールは`scripts/<プロジェクト名>/`に1ファイル=1ツールで置き、
次のように実行する。

```bash
uv run python scripts/<プロジェクト名>/<ツール名>.py [オプション]
```

各ツールの処理概要・入出力・実行オプションは
`docs/<プロジェクト名>/<ツール名>.md`に説明資料を用意する（本採用時に上表を
更新する）。

新しいツールを追加するときのルールは[CLAUDE.md](CLAUDE.md)を参照
（要点: ツールを追加・変更したら対応する説明資料も必ず更新する）。

## 構成

フォルダ構成の詳細は
[docs/repository-structure.md](docs/repository-structure.md)を参照。

