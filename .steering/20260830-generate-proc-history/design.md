# design.md — proc_history サンプルデータ生成ツールの新規作成

## 実装アプローチ

`docs/reference/`配下に、既存の`generate_sample_data`と同じ位置づけ
（4ステップ構成の例外＝`cli.py`/`io.py`+処理本体、`src/`本採用前の参考実装）で
`generate_proc_history`を追加する。

`proc_history`は「品目階層（`prodspec_id`→`mainpd_id`）」「ルーティング
（`mainpd_id`ごとの`ope_no`×`ope_seq`の並び）」「設備ごとに固定の処理時間」
「ロット内で時系列が単調増加する」という、テーブル内の行間・列間に依存関係を
持つ。既存`generate_sample_data`の「列ごとに独立して乱数を引く」方式では
これを表現できないため、`DatasetProfile`とは別の専用設定フォーマット
（`ProcHistoryConfig`）と、ロット単位でルーティングに沿って時刻を進めながら
行を生成する専用ロジックを新規実装する。

生成の骨子（`generate.py`内で完結、いずれも「データを受け取り値を返す」純粋
関数として分割する）:

1. `prodspec_id`（30種類）のマスタを作る
2. `prodspec_id`ごとに`mainpd_id`を複数生成し、親子関係を持つマスタを作る
3. `eqp_id`（設備）のマスタを作り、**設備ごとに1個だけ**固定処理時間
   （分）を乱数で割り当てる（以後、その設備を使う限り常にこの値を使う）
4. `ope_name_pool`から、`mainpd_id`ごとに専用のルーティング（`ope_no`の
   並び、`ope_seq`はその並び順）を組み立てる。各`ope_no`には、
   使用可能な`eqp_id`の候補群（`ope_no`単位で固定、複数の`mainpd_id`の
   ルーティングで使い回される）を割り当てる
5. `lot_count`ぶんのロットに、`mainpd_id`をランダムに割り当てる（今回は
   一様分布。品目ごとの生産量に偏りを持たせたい場合は将来拡張とする）
6. ロットごとに、`time_range`内のランダムな時刻を「そのロットの最初の工程の
   `start_time`」として決め、ルーティングの`ope_seq`順に工程を1つずつ
   処理する。各工程では
   - `ope_no`の候補`eqp_id`群からランダムに1つ選ぶ
   - その`eqp_id`の固定処理時間から`end_time = start_time + 処理時間`を
     決める
   - `queue_minutes`を分布からサンプリングし、
     `次工程のstart_time = end_time + queue_minutes`（`queue_minutes`は
     必ず正の値）とすることで、**次工程の開始が必ず前工程の終了より
     後ろになる**ことを保証する
   - 行（`lot_id`/`prodspec_id`/`mainpd_id`/`ope_no`/`ope_seq`/`eqp_id`/
     `start_time`/`end_time`）を1件積む
7. 全ロットぶんの行をまとめて`pyarrow.Table`にし、Parquetへ書き出す

行数が数万件規模（`lot_count`×平均工程数）を想定しており、
`generate_sample_data`のようなチャンク分割書き出しは不要。一度に
`pyarrow.Table`を組み立ててから1回で書き出す。書き出しは
`docs/development-guidelines.md`の「出力ファイルの安全な書き込み」に従い、
一時ファイルに書いてから成功時のみ`os.replace()`でリネームする（既存の
`generate_sample_data`参考実装はこの規約に沿っていないが、今回は新規実装
として規約を満たす）。

## 変更するコンポーネント（新規作成のみ、既存ファイルの変更は無し）

```text
docs/reference/
├── generate_proc_history.py            # エントリポイント
├── generate_proc_history.md            # 説明資料（処理概要/IO/実行オプション）
└── analyse_tool/generate_proc_history/
    ├── __init__.py                     # main()：cli→config読込→生成→書き出し
    ├── cli.py                          # 引数定義（--config/--output/--seed/--lot-count）
    ├── config.py                       # ProcHistoryConfig（設定JSONのデータ構造・読込）
    ├── io.py                           # 設定読込・Parquet安全書き込み
    └── generate.py                     # 生成ロジック本体（上記1〜7の純粋関数群）

profiles/
└── proc_history_config.json            # ProcHistoryConfigの実体（後述）
```

- `common/`配下の既存モジュール（`profile.py`/`report.py`/`charts/`）は
  変更しない。`ProcHistoryConfig`は`DatasetProfile`と別物のため、
  `common/profile.py`には追加しない（このツール専用のため
  `generate_proc_history/config.py`に閉じる）。
- 既存の`generate_sample_data`・`customer_pref_summary`とのファイル共有・
  相互依存も発生させない（`docs/architecture.md`の設計原則を踏襲）。

## データ構造の変更

### 設定ファイル: `profiles/proc_history_config.json`（新形式・`ProcHistoryConfig`）

```jsonc
{
  "name": "proc_history",
  "prodspec_count": 30,
  "mainpd_per_prodspec": { "min": 2, "max": 6 },
  "ope_name_pool": ["受入", "前処理", "主加工", "組立", "調整", "外観検査", "機能検査", "梱包", "出荷検査"],
  "steps_per_routing": { "min": 5, "max": 8 },
  "eqp_count": 24,
  "eqp_per_ope_name": 4,
  "eqp_processing_minutes": { "distribution": "lognormal", "mean": 40, "stddev": 10, "min": 10, "max": 120 },
  "queue_minutes": { "distribution": "lognormal", "mean": 30, "stddev": 60, "min": 1, "max": 4320 },
  "lot_count": 5000,
  "time_range": { "start": "2026-01-01T00:00:00", "end": "2026-06-30T23:59:59" }
}
```

- `mean`/`stddev`は`common/profile.py`の`lognormal`と同じ扱い（対数正規分布の
  元になる正規分布側のパラメータ）とし、`min`/`max`でクリップする。
- `seed`は`DatasetProfile`同様に設定ファイルへ持たせず、`generate_sample_data`
  に揃えて**CLI引数`--seed`（既定0）**でのみ指定する。
- `lot_count`は`generate_sample_data`の`--rows`に相当するものとして、
  CLI引数`--lot-count`で上書き可能にする（省略時は設定ファイルの値を使う）。

`config.py`には`ProcHistoryConfig`（および`MinMax`・`LognormalSpec`等の
小さいデータクラス）を定義し、`to_dict()`/`from_dict()`（または
`load_config()`）を持たせる。実装は`common/profile.py`の
`DatasetProfile`/`ColumnProfile`と同じ書き方（`dataclass`＋`from __future__
import annotations`）に揃える。

### 出力テーブル: `proc_history`（requirements.mdに記載済みのスキーマのまま。変更なし）

## 影響範囲の分析

- **既存コードへの影響**: 無し（新規ファイルの追加のみ）。
- **永続的ドキュメント（`docs/`）への影響**: requirements.mdで判断した通り、
  「データそのものを作るユーティリティ」という既存の例外パターン
  （`docs/functional-design.md`記載）の範囲内のため、更新不要と判断する。
- **テストについて**: `docs/development-guidelines.md`のテスト規約では
  「純粋な実装には必ずユニットテストを書く」とされているが、既存の参考実装
  （`generate_sample_data`/`customer_pref_summary`）も`docs/reference/`配下に
  ある間はテストを持たない運用になっている（`tests/`ディレクトリ自体が
  未作成）。今回もこの前例を踏襲し、`docs/reference/`段階ではユニット
  テストを追加せず、後述の「検証」（生成結果に対するDuckDBでの確認クエリ）
  で品質を担保する。`src/`への本採用時に、他の参考実装とまとめて
  `tests/`配下にユニットテストを追加する（`docs/product-requirements.md`の
  「既知のリスク」に記載されている、参考実装と本採用の乖離リスクと同種の
  扱いとする）。
- **依存パッケージ**: 追加は不要（`numpy`/`pyarrow`は`pyproject.toml`に
  既存）。

## 検証方法（実装後に実施）

1. 生成コマンドが完了すること
   ```bash
   PYTHONPATH=docs/reference uv run python docs/reference/generate_proc_history.py \
     --config profiles/proc_history_config.json \
     --output output/proc_history_sample.parquet
   ```
2. DuckDBで以下を確認する
   - 総行数が`lot_count`×平均工程数に近いこと
   - ロットごとに`ope_seq`が1から連番で欠番なく並んでいること
   - 同一ロット内で工程`N+1`の`start_time`が工程`N`の`end_time`より
     常に後ろになっていること（同時刻・逆転がないこと）
   - 同じ`eqp_id`を使った行はどれも`end_time - start_time`が同一の固定値に
     なっていること
   - `mainpd_id`が常に想定した`prodspec_id`の子として一貫していること
