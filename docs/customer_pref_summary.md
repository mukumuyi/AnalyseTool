# customer_pref_summary 説明資料

- 対応スクリプト: `scripts/customer_pref_summary.py`
- 作成日 / 更新日: 2026-08-29

## 処理概要

顧客マスタ（customers）を地方区分（`pref`）ごとに集計し、顧客数の多い順に
並べた積み上げ棒グラフを作る。棒は顧客区分（`segment`）で色分けし、棒を
クリックするとその内訳（該当する `pref`×`segment` の顧客明細）が下に
表示されるインタラクティブなHTMLレポートを出力する。

| ステップ | 一般的な呼称 | モジュール | このスクリプトでの内容 |
| --- | --- | --- | --- |
| ① 前準備 | EDA（探索的データ分析） | `prepare.py` | `profile_from_parquet()` で件数・欠損率・カテゴリ分布などを確認 |
| ② データ加工 | データクレンジング/前処理 | `process.py` | `pref`/`segment`欠損行の除外、`customer_id`重複除去 |
| ③ 分析 | 分析・モデリング | `analyze.py` | `pref`×`segment`件数集計、`pref`総数降順の並び順算出、明細データ抽出 |
| ④ 可視化 | 可視化・レポーティング | `visualize.py` | 積み上げ棒グラフ（`common/charts/bar.py`）＋クリック連動明細表（`common/report.py`）のHTMLレポート出力 |

## I/O説明

### 入力

| 項目 | 内容 |
| --- | --- |
| `--input` | 顧客マスタのParquetファイルパス（既定: `output/customers_sample.parquet`） |
| 必須カラム | `customer_id`（顧客ID）, `customer_name`（顧客名）, `segment`（顧客区分：個人/法人/官公庁/その他）, `pref`（地方区分：北海道〜九州・沖縄の8区分） |
| 前提条件 | 事前に `generate_sample_data`（`profiles/customers.json`）等でParquetを用意しておく |

### 出力

| 項目 | 内容 |
| --- | --- |
| `--output` | レポートHTML（既定: `output/customer_pref_summary.html`）。`file://`で直接開ける自己完結HTML |
| `--profile-output` | 前準備(EDA)の傾向プロファイルJSON（既定: `output/customer_pref_summary_profile.json`）。`DatasetProfile`形式 |
| レポートの内容 | 横軸=`pref`（顧客総数の多い順）、縦軸=顧客数、色=`segment`の積み上げ棒グラフ。棒をクリックすると、その`pref`×`segment`に該当する顧客明細（`customer_id`/`customer_name`/`segment`/`pref`）が表として表示される（1回のクリックで最大2000行まで表示、超過時はその旨を注記） |
| 副作用 | `--output`・`--profile-output`とも既存ファイルがあれば上書きする |

## 実行オプション

```bash
uv run python scripts/customer_pref_summary.py \
  --input output/customers_sample.parquet \
  --output output/customer_pref_summary.html \
  --profile-output output/customer_pref_summary_profile.json
```

| オプション | 既定値 | 説明 |
| --- | --- | --- |
| `--input` | `output/customers_sample.parquet` | 顧客マスタのParquetファイルパス |
| `--output` | `output/customer_pref_summary.html` | 出力するレポートHTMLのパス |
| `--profile-output` | `output/customer_pref_summary_profile.json` | 前準備(EDA)のプロファイルJSON出力パス |

## 既知の制約・注意点

- 明細データ（`customer_id`/`customer_name`/`segment`/`pref`）は全顧客ぶんを
  HTMLにJSONとして埋め込み、クリック時の絞り込みはブラウザ側JSで行う。顧客数が
  数十万件を超えるような規模になるとHTMLサイズ・ブラウザ負荷が大きくなるため、
  その場合は`analyze.py`側で明細を絞り込む・別ファイルに分離するなどの対応が
  別途必要になる（現状は顧客マスタ想定の数千〜数万件規模を前提）。
- 棒グラフのクリック判定は、クリックしたトレース名（`segment`の値）と
  横軸カテゴリ（`pref`の値）の組み合わせで明細を絞り込んでいる
  （`common/report.py` の `build_bar_click_detail_html()`）。
