# AnalyseTool

DATA分析で使うツールスクリプトを溜めていく社内ツール集。目的・背景は
[docs/product-requirements.md](docs/product-requirements.md)を参照。

## セットアップ

```bash
uv sync
```

## 現在の状態

まだ`src/`・`scripts/`への本採用は行われておらず、動作確認済みの試作実装が
[docs/reference/](docs/reference/)に置かれている段階です。

| ツール | 状態 | 説明資料 | 概要 |
| --- | --- | --- | --- |
| `generate_sample_data` | リファレンス実装（`docs/reference/`） | [docs/reference/generate_sample_data.md](docs/reference/generate_sample_data.md) | データ定義情報（プロファイル）からサンプルデータ（Parquet）を生成する |
| `customer_pref_summary` | リファレンス実装（`docs/reference/`） | [docs/reference/customer_pref_summary.md](docs/reference/customer_pref_summary.md) | 顧客マスタをprefごとに集計し、segment色分け・クリックで明細が見える棒グラフレポートを作る |

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
