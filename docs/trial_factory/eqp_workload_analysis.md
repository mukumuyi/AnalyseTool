# eqp_workload_analysis 説明資料

- 対応スクリプト: `scripts/trial_factory/eqp_workload_analysis.py`
- 作成日 / 更新日: 2026-08-31

## 処理概要

`proc_history`（ロット×工程×設備の工程実績履歴）を対象に、設備ごとの
処理数・ロット待機時間を集計し、負荷の高い設備をパレート図で示す。
パレート図の棒をクリックすると、その設備の時間帯別稼働状況（装置稼働
グラフ）→ガントチャート＋仕掛数量推移→ロット明細表、と4段階で
掘り下げられるインタラクティブなHTMLレポートを出力する。

| ステップ | 一般的な呼称 | モジュール | このスクリプトでの内容 |
| --- | --- | --- | --- |
| ① 前準備 | EDA（探索的データ分析） | `prepare.py` | `profile_from_parquet()`で件数・欠損率・カテゴリ分布などを確認 |
| ② データ加工 | データクレンジング/前処理 | `process.py` | 必須列の欠損除去・型整形、`wait_minutes`/`next_eqp_id`/`prev_eqp_id`の付与 |
| ③ 分析 | 分析・モデリング | `analyze.py` | 設備ごとの処理数・待機時間集計、パレート、代表期間の時間帯別集計・ロット明細抽出 |
| ④ 可視化 | 可視化・レポーティング | `visualize.py` | ①〜⑥の6セクションを1枚の自己完結HTMLレポートに組み立て |

## I/O説明

### 入力

| 項目 | 内容 |
| --- | --- |
| `--input` | `proc_history`のParquetファイルパス（既定: `data/trial_factory/proc_history.parquet`） |
| 必須カラム | `lot_id`/`prodspec_id`/`mainpd_id`/`ope_no`/`ope_seq`/`eqp_id`/`start_time`/`end_time` |
| 前提条件 | `generate_proc_history`（`docs/reference/`）等で生成したサンプルデータを想定 |

### 出力

| 項目 | 内容 |
| --- | --- |
| `--output-dir` | 出力ルートディレクトリ（既定: `output`）。この配下の`trial_factory/<実行日>/`にレポート・プロファイルを書き出す |
| レポート | `<実行日>/eqp_workload_analysis_<実行時刻>.html`（`file://`で直接開ける自己完結HTML） |
| プロファイル | `<実行日>/eqp_workload_analysis_profile_<実行時刻>.json`（`DatasetProfile`形式） |
| レポートの内容 | ①設備ごとの処理数、②③待機時間（合計・平均）、④⑤処理数×待機時間の散布図（いずれも上位設備に絞り込んだ棒・散布図）、⑥パレート図→装置稼働グラフ→ガントチャート＋仕掛数量推移→ロット明細表の4段階ドリルダウン |
| 副作用 | `--output-dir`配下に新規ファイルを書き出す（同名上書きはしない。実行時刻がファイル名に入るため）。`output/trial_factory/index.html`に実行結果を追記登録する |

## 実行オプション

```bash
uv run python scripts/trial_factory/eqp_workload_analysis.py \
  --input data/trial_factory/proc_history.parquet \
  --output-dir output
```

| オプション | 既定値 | 説明 |
| --- | --- | --- |
| `--input` | `data/trial_factory/proc_history.parquet` | `proc_history`のParquetファイルパス |
| `--output-dir` | `output` | 出力ルートディレクトリ |
| `--top-n` | `15` | パレート図・ドリルダウンの対象にする上位設備数（待機時間合計の多い順） |
| `--period-days` | `3` | 装置稼働グラフ（⑥-2）の代表期間（日数） |
| `--gantt-window-hours` | `4` | ガントチャート（⑥-3）の初期表示窓幅（時間） |

## 既知の制約・注意点

- 対象は実データではなく、`generate_proc_history`（`docs/reference/`）で
  生成したサンプルデータを前提とする。
- サンプルデータは設備の同時使用制約（1台1ロット）を持たないため、
  ガントチャートの並行処理枠（行）数が実際の工場のバッチ挙動より多く
  出ることがある（レポート上部に注記を表示する）。
- ガントチャート・仕掛数量推移の「故障」ステータスは、`proc_history`の
  現行データモデルに設備の停止理由・ダウンタイム情報が無いため対象外
  （着工中／待機の2ステータスのみ）。
- ⑥-3・⑥-4（ガントチャート＋仕掛数量推移、ロット明細表）は、上位設備
  ×代表期間で絞り込んだ`LotDetail`（数千行規模）をHTMLにJSONとして
  埋め込み、クリックのたびにブラウザ側のJavaScriptが図・表を組み立てる
  （「構築式」。`common/report.py`参照）。全設備・全期間のロット明細を
  埋め込む用途は想定していない。
