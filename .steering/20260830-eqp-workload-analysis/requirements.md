# requirements.md — 設備稼働負荷・ロット待機分析ツールの新規開発（初回本採用）

## 背景

`generate_proc_history`（`docs/reference/`の参考実装）で生成した
`proc_history`（ロット×工程×設備の工程実績履歴）データを対象に、
「設備ごとの稼働負荷」「ロットの工程間待機時間」を集計・可視化する分析
ツールを開発する案件。

前回のセッションで`eqp_workload_analysis`という名前の試作が動作しており、
`output/trial_factory/20260830/`配下に生成済みレポート（HTML）が3件残って
いる。しかし**そのPythonソースコードはリポジトリ上に存在せず**（コミット
履歴・`docs/reference/`・`src/`のいずれにも無い）、生成物のみが現存する
状態だった。今回はこの生成物を仕様のラフ案として引き継ぎつつ、ソースを
正式に作り直す。

あわせて、本リポジトリでは`src/`+`scripts/`への「本採用」（`プロジェクト`
という単位での正式配置）がまだ1件も行われていない
（`docs/repository-structure.md`参照）。本ツールを最初の本採用案件とし、
プロジェクト名を`trial_factory`（既存の`data/trial_factory/`・
`output/trial_factory/`に合わせる）とする。

## 変更・追加する機能の説明

- `src/analyse_tool/trial_factory/eqp_workload_analysis/` +
  `scripts/trial_factory/eqp_workload_analysis.py` として、
  `prepare`/`process`/`analyze`/`visualize`の4ステップ構成で新規実装する。
- 入力は`generate_proc_history`が生成した`proc_history`のParquet
  （`data/trial_factory/proc_history.parquet`）。
- 前回試作の出力から読み取れる、次のグラフ構成を土台にする
  （下記「画面イメージ（ラフ）」も参照）。
  1. 設備ごとの処理数
  2. 設備ごとのロット待機時間（合計）
  3. 設備ごとのロット待機時間（平均）
  4. 処理数 × 待機時間（合計）の関係
  5. 処理数 × 待機時間（平均）の関係
  6. 負荷の高い設備をパレート図で示し、クリックした設備の時間帯別
     稼働状況をタイムラインとして下に表示するドリルダウン
- 上記のうち、パレート図・タイムラインは`common/charts/`に未実装
  （`docs/functional-design.md`で「設計合意済み・未実装」）のため、
  本ツールの実装と合わせて`common/charts/pareto.py`・
  `common/charts/timeline.py`を新規実装する。
- 「ロット待機時間」は`proc_history`に列として存在しないため、
  同一ロット内で工程`N`の`end_time`と工程`N+1`の`start_time`の差分から
  `process.py`で算出する（`generate_proc_history`側の生成ルールとして
  時系列が単調増加することは保証済み）。

## ユーザーストーリー

- 分析担当者として、`proc_history`データから設備ごとの処理件数・
  ロット待機時間の負荷傾向を把握したい。
- 分析担当者として、負荷の高い設備をパレート図で一目で把握し、気になる
  設備をクリックしてその設備の時間帯別の稼働状況（タイムライン）を
  確認したい。
- 分析担当者として、処理数が多い設備ほど待機時間も長いのか（相関）を
  散布図で確認したい。

## 受け入れ条件

- `data/trial_factory/proc_history.parquet`を入力に、
  `prepare`→`process`→`analyze`→`visualize`の4ステップで実装されている
  こと（`docs/product-requirements.md`の受け入れ条件に準拠）
- `prepare`/`process`がDuckDBのSQL集計で完結し、pandas全件ロードを
  しないこと（数百万行規模の`proc_history`を想定）
- 出力は`file://`で開ける自己完結HTMLレポートであり、
  `output/trial_factory/<YYYYMMDD>/`配下に実行時刻付きファイル名で
  書き出され、`output/trial_factory/index.html`に追記登録されること
- 「画面イメージ（ラフ）」に挙げた6種のグラフ・ドリルダウンが実装されて
  いること
- 全設備・全期間をそのまま初期表示すると密集して読めなくなる場合、
  上位N件への絞り込みなどの対策が講じられていること（`design.md`で確定）
- 対応する説明資料`docs/trial_factory/eqp_workload_analysis.md`を作成する
  こと
- `ruff check`/`ruff format`/`mypy`/`pytest`が通ること。純粋な集計・
  変換ロジックにはユニットテストを書くこと

## 制約事項

- 実データではなく、`generate_proc_history`（`docs/reference/`）で
  生成したサンプルデータ（`data/trial_factory/proc_history.parquet`）を
  対象とする
- 前回試作のソースは存在しないため、残っているHTML出力からの読み取りと
  今回の設計判断で作り直す。前回試作との完全な見た目の一致は保証しない
- `common/charts/`・`common/report.py`など全プロジェクト横断の共通処理を
  新規実装・変更する場合、`customer_pref_summary`など他の参考実装との
  互換性を壊さない（既存の関数シグネチャを破壊的に変更しない）
- 永続的ドキュメントへの影響: 本採用は`docs/repository-structure.md`が
  「タイミングは本採用時に判断する」としていた事項の実行にあたるため、
  実装後に`docs/repository-structure.md`（プロジェクト名の確定・
  `docs/reference/`移行期記述の扱い）・`docs/product-requirements.md`
  （「既知のリスク」の`docs/reference/`乖離リスクの扱い）を見直す
  （`design.md`で影響範囲を確定する）

## 画面イメージ（ラフ）

前回試作の生成物`output/trial_factory/20260830/eqp_workload_analysis_142708.html`
を、今回のラフ案としてそのまま添付する（ユーザーへのファイル送付を参照）。
構成は次の通り（上から縦に並ぶ1カラムのレポート）。

```
┌─────────────────────────────────────────┐
│ 設備稼働負荷・ロット待機分析                    │
├─────────────────────────────────────────┤
│ [棒グラフ] 設備ごとの処理数                     │
├─────────────────────────────────────────┤
│ [棒グラフ] 設備ごとのロット待機時間（合計）        │
├─────────────────────────────────────────┤
│ [棒グラフ] 設備ごとのロット待機時間（平均）        │
├─────────────────────────────────────────┤
│ [散布図]  処理数 × 待機時間（合計）              │
├─────────────────────────────────────────┤
│ [散布図]  処理数 × 待機時間（平均）              │
├─────────────────────────────────────────┤
│ [パレート図] 設備別タイムライン                  │
│  → 棒をクリックすると、その設備の時間帯別          │
│    稼働状況（積み上げ棒＋着工件数の折れ線）が       │
│    下に表示される                             │
└─────────────────────────────────────────┘
```

このラフはあくまで前回試作からの読み取りであり、細部（上位何件に絞るか、
グラフの軸・配色・タイムラインの粒度等）は`design.md`で確定させる。
