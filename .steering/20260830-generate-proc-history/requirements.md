# requirements.md — proc_history サンプルデータ生成ツールの新規作成

## 背景

「工場でロット着工できない理由の分析」を初期開発の題材として選定した。
対象データに近いKaggle等の公開データセットは見つからなかったため、実際の
業務データ構造（`proc_history`：ロット×工程×設備の工程実績履歴）をヒアリング
した上で、サンプルデータを合成する方針とした。

`proc_history`は列内・行間に依存関係（時系列の単調増加、設備ごとに固定の
処理時間）があり、既存の`generate_sample_data`（列ごとに独立して値を生成する
方式）ではこの依存関係を再現できない。そのため、`proc_history`専用の生成
ロジックを新規に実装する。

## 変更・追加する機能の説明

`docs/reference/`配下に、`proc_history`テーブルのサンプルデータ（Parquet）を
生成する新しい参考実装を追加する。既存の`generate_sample_data`と同じく、
「データそのものを作る」ユーティリティ（4ステップ構成の対象外）として扱う。

### 生成されるテーブル: `proc_history`

| 列名 | dtype | 内容 |
| --- | --- | --- |
| `lot_id` | string | ロットID（`LOT000001`のような連番） |
| `prodspec_id` | string | 品目ID（親、30種類固定） |
| `mainpd_id` | string | 主品目ID（子、`prodspec_id`ごとに複数） |
| `ope_no` | string | 作業名（テキスト、数字を含まない） |
| `ope_seq` | int | `mainpd_id`内での作業順序（1,2,3...） |
| `eqp_id` | string | 設備ID |
| `start_time` | datetime | その工程の開始時刻 |
| `end_time` | datetime | その工程の終了時刻 |

### 満たすべきデータ特性

- `prodspec_id`が親、`mainpd_id`が子という階層を持つ（1つの`prodspec_id`に
  複数の`mainpd_id`がぶら下がる）
- 各`mainpd_id`は固有のルーティング（`ope_no`×`ope_seq`の並び）を持ち、
  そのルーティングに沿ったロットの`proc_history`行が生成される
- **設備の処理時間は設備ごとに固定・作業内容に依らない**：同じ`eqp_id`なら
  `ope_no`が何であっても処理時間（`end_time - start_time`）は同じ値になる。
  設備が異なれば時間が異なってよい（設備の性能差の表現）
- **ロット内で工程は必ず時系列順に進む**：同一ロットの工程`N+1`の
  `start_time`は、工程`N`の`end_time`より必ず後ろになる（同時刻・逆転・
  重複を許容しない）
- 「理由コード」を持つテーブルは今回のスコープに含めない（`proc_history`
  単体のみを対象とする）

## ユーザーストーリー

- 分析担当者として、実データがまだ無い状態でも`proc_history`のサンプル
  データを生成し、「ロットの着工待ち時間（工程間ギャップ）」を集計・可視化
  する分析ツールの実装を先に進めたい。

## 受け入れ条件

- 設定ファイル（`profiles/proc_history_config.json`）を読み込み、
  `proc_history`のParquetファイルを生成できること
- 設定ファイルは既存の`DatasetProfile`形式とは別の、本ツール専用の形式で
  よい（列ごとに独立生成という`DatasetProfile`の前提がこのテーブルには
  合わないため）
- 生成結果が「満たすべきデータ特性」（上記）を全て満たすこと
- 生成規模は数百万行を想定しない（動作確認できる規模＝数万行程度から
  開始する）
- 対応する説明資料を作成すること（`docs/reference/generate_proc_history.md`
  など、既存の`generate_sample_data.md`に準じた内容）

## 制約事項

- 既存の`generate_sample_data`・`customer_pref_summary`とツール間の相互
  依存は作らない（`docs/architecture.md`の設計原則を踏襲）
- `src/`・`scripts/`への本採用はまだ行わない（既存の`docs/reference/`配下の
  参考実装として追加する）。本採用のタイミングは別途判断する
- 永続的ドキュメント（`docs/product-requirements.md`等）への影響: 本ツールは
  既存の「データそのものを作るユーティリティ」という例外パターン
  （`docs/functional-design.md`に記載済み）の範囲内に収まるため、基本設計への
  影響は無いと判断し、永続的ドキュメントの更新は行わない
