# generate_sample_data 説明資料

- 対応スクリプト: `scripts/generate_sample_data.py`
- 作成日 / 更新日: 2026-08-29

## 処理概要

「データ定義情報（プロファイル）」というJSONファイルを読み込み、そこに書かれた
列ごとの型・分布・カテゴリ値などに従ってサンプルデータを生成し、Parquetとして
出力する。分析ツール（EDA/加工/分析/可視化の4ステップ）を試すためのテストデータ
作成用ユーティリティで、本ツール自体は4ステップ構成ではなく
`cli.py`（引数） / `io.py`（読み書き） / `generate.py`（生成ロジック）の
3モジュール構成にしている。

プロファイルのフォーマットは `src/analyse_tool/common/profile.py` の
`DatasetProfile` / `ColumnProfile` で定義しており、各分析ツールの
`prepare.py`（EDA）が実データから `profile_from_parquet()` で自動生成する
出力と**同じフォーマット**。つまり「実データをプロファイリングして得た定義」も
「人が手で書いた定義」も、同じ形式でこのツールへの入力にできる。

数百万〜数億行を想定し、`CHUNK_ROWS`（既定100万行）ごとに生成してParquetへ
追記書き出しすることで、メモリ使用量を一定に抑えている。

## I/O説明

### 入力

| 項目 | 内容 |
| --- | --- |
| `--profile` | データ定義情報（プロファイル）のJSONファイルパス。`profiles/` 配下の例、または各ツールの `prepare.py` が出力したもの |
| 必須スキーマ | `DatasetProfile`（`name`, `row_count`, `columns[]`）。各列は `role`（`id`/`numeric`/`categorical`/`date`/`boolean`）に応じたフィールドを持つ。詳細は `src/analyse_tool/common/profile.py` の docstring を参照 |

### 出力

| 項目 | 内容 |
| --- | --- |
| ファイル | `--output` で指定したParquetファイル（例: `output/orders_sample.parquet`） |
| 内容 | プロファイルで定義した列を、指定行数ぶん生成したテーブル |
| 副作用 | 既存ファイルがあれば上書きする |

## 実行オプション

```bash
uv run python scripts/generate_sample_data.py \
  --profile profiles/orders.json \
  --output output/orders_sample.parquet \
  --rows 10000000 \
  --seed 0
```

| オプション | 既定値 | 説明 |
| --- | --- | --- |
| `--profile` | (必須) | データ定義情報（プロファイル）のJSONパス |
| `--output` | (必須) | 出力先Parquetファイルパス |
| `--rows` | プロファイルの `row_count` | 生成する行数。大量データでの動作確認用に上書き可能（例: `100000000` で1億行） |
| `--seed` | `0` | 乱数シード。同じ値なら同じデータを再現できる |

### 用意している例

`profiles/customers.json`（顧客マスタ、既定1万行）、`profiles/orders.json`
（注文明細、既定100万行）。顧客区分・地域・商品カテゴリなどを持つ汎用的な
業務データの構成で、`--rows` を大きくすれば大量データ動作確認にも使える。

## 既知の制約・注意点

- `role` ごとの生成ロジックは簡易的なもの（`numeric`: 一様/正規/対数正規、
  `categorical`: 出現割合に従った選択、`date`: 範囲内の一様乱数など）。
  実データの相関関係（例: カテゴリと金額の関係）までは再現しない。
- `common/profile.py` の `profile_from_parquet()` は型と distinct 件数からの
  簡易的な推定（ヒューリスティック）で `role` を決めるため、値の種類が少ない
  数値列（例: 個数など）は `numeric` ではなく `categorical` と判定されることが
  ある。厳密に再現したい場合はプロファイルJSONを手で調整する。
