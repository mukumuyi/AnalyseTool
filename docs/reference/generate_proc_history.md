# generate_proc_history 説明資料

- 対応スクリプト: `docs/reference/generate_proc_history/`（`python -m`で実行）
- 作成日 / 更新日: 2026-08-30

## 処理概要

工場の「ロット×工程×設備」の工程実績履歴（`proc_history`）のサンプルデータを
作るツール。品目階層（`prodspec_id`→`mainpd_id`）・工程ルーティング
（`ope_no`×`ope_seq`）・設備ごとに固定の処理時間・ロット内で時系列が単調
増加する待ち時間、という行間・列間の依存関係を持つデータのため、
`generate_sample_data`（列ごとに独立して値を生成する方式）とは別の専用
ロジックとして実装している。

生成の流れ：①`prodspec_id`×`mainpd_id`の階層マスタを作る → ②設備マスタ
（`eqp_id`ごとに固定処理時間を1つ割り当てる）を作る → ③`mainpd_id`ごとに
ルーティング（`ope_no`の並びと候補`eqp_id`群）を作る → ④ロットに`mainpd_id`
を割り当てる → ⑤ロットごとにルーティングに沿って時刻を進めながら行を生成する
→ ⑥生成結果が決めたルールを守っているかを`validate.py`で自動検証する →
⑦問題が無ければParquetへ書き出す。

| モジュール | 役割 |
| --- | --- |
| `cli.py` | 引数定義 |
| `config.py` | 設定フォーマット`ProcHistoryConfig`の定義・読込 |
| `generate.py` | 生成ロジック本体 |
| `validate.py` | 生成結果が生成ルールを守っているかの自動検証 |
| `io.py` | 設定読込・Parquetの安全な書き込み |
| `__init__.py`/`__main__.py` | エントリポイント（`main()`：読込→生成→検証→書き出し） |

## I/O説明

### 入力

| 項目 | 内容 |
| --- | --- |
| `--config` | `proc_history`生成用の設定JSON（`ProcHistoryConfig`形式）のパス。`profiles/proc_history_config.json`が例 |
| 必須スキーマ | `name`/`prodspec_count`/`mainpd_per_prodspec`/`ope_name_pool`/`steps_per_routing`/`eqp_count`/`eqp_per_ope_name`/`eqp_processing_minutes`/`queue_minutes`/`lot_count`/`time_range`。詳細は`config.py`のdocstringを参照 |

`ProcHistoryConfig`は`common/profile.py`の`DatasetProfile`とは**別形式**。
`DatasetProfile`は列ごとに独立して値を生成する前提のため、`proc_history`の
親子階層・ルーティング・時系列依存を表現できない。

### 出力

| 項目 | 内容 |
| --- | --- |
| `--output` | 出力先Parquetファイルパス（例: `output/proc_history_sample.parquet`） |
| 生成される列 | `lot_id`/`prodspec_id`/`mainpd_id`/`ope_no`/`ope_seq`/`eqp_id`/`start_time`/`end_time` |
| 副作用 | 既存ファイルがあれば上書きする（一時ファイルに書いてから`os.replace()`でリネームするため、書き込み中の異常終了で壊れたファイルが残ることはない） |
| 検証失敗時 | 生成結果が生成ルールに違反している場合、違反内容を標準出力に表示し、Parquetを書き出さずに異常終了する（終了コード1） |

## 実行オプション

```bash
PYTHONPATH=docs/reference uv run python -m generate_proc_history \
  --config profiles/proc_history_config.json \
  --output output/proc_history_sample.parquet \
  --lot-count 5000 \
  --seed 0
```

| オプション | 既定値 | 説明 |
| --- | --- | --- |
| `--config` | (必須) | `ProcHistoryConfig`のJSONパス |
| `--output` | (必須) | 出力先Parquetファイルパス |
| `--lot-count` | 設定ファイルの`lot_count` | 生成するロット数。省略時は設定ファイルの値を使う |
| `--seed` | `0` | 乱数シード。同じ値なら同じデータを再現できる |

## 生成ルール（`validate.py`が自動検証する内容）

- 全行で`start_time < end_time`が成り立つ
- ロットごとに`ope_seq`が1から欠番・重複なく連番になっている
- 同一ロット内で、工程`N+1`の`start_time`が工程`N`の`end_time`より
  必ず後ろになっている（同時刻・逆転が無い）
- 同じ`eqp_id`を使った行はすべて`end_time - start_time`（マイクロ秒単位の
  厳密な差分）が同一の固定値になっている（設備ごとの処理時間が一定）
- `mainpd_id`は常に同じ`prodspec_id`に紐づいている

## 既知の制約・注意点

- **`mean`/`stddev`は対数正規分布の元になる正規分布側のパラメータ**
  （`common/profile.py`の`lognormal`と同じ扱い）。「平均40分」にしたい
  場合は`mean`に`40`ではなく`ln(40)≈3.6889`を設定する必要がある
  （`40`をそのまま入れると値がほぼ全て`max`に張り付く）。
  `profiles/proc_history_config.json`は実際に分布を確認した上でこの
  換算済みの値を設定している。
- `end_time - start_time`の一致判定はDuckDBの`INTERVAL`（マイクロ秒精度）
  同士の厳密一致で行っている。`date_diff('minute', ...)`のような分単位への
  丸めでは、`start_time`の秒未満の端数によって同じ固定処理時間でも異なる
  分数に見えることがあるため、検証や集計に使わないこと。
- ロットへの`mainpd_id`割当は現状一様分布（品目ごとの生産量に偏りは無い）。
  偏りを持たせたい場合は`generate.py`の`_assign_lot_mainpd()`の拡張が必要。
- 各ロットの開始時刻は`time_range`内の一様乱数のため、ルーティングの
  工程数・待ち時間次第では最後の工程の`end_time`が`time_range.end`を
  超えることがある（意図的な許容。サンプルデータとしては問題無い）。
- `ope_no`（作業名）・`prodspec_id`/`eqp_id`の命名や件数は仮の値。実際の
  値一覧が分かった場合は`profiles/proc_history_config.json`の該当値を
  差し替えるだけでよい。
- `steps_per_routing`（現在600〜800）が`ope_name_pool`の件数より大きい
  場合、`_build_routing()`は同じ`ope_no`を繰り返し使う（重複あり）。
  半導体工程のように少数の工程種別を何百回も通過する実態を想定した挙動。
- `eqp_per_ope_name`は`{min, max}`の範囲指定（`ope_no`ごとに個別に台数を
  決める）。候補設備の割当は「①全`eqp_id`をシャッフルして`ope_no`に
  ラウンドロビンで1台ずつ配る（構造的に全設備を最低1回はどこかの候補に
  入れる）→②`ope_no`ごとの目標台数（`eqp_per_ope_name`）に足りない分を
  追加抽選する」という2段階方式（`_build_ope_eqp_candidates()`）のため、
  **`eqp_count`（設備総数）を増やしても全設備が候補に入ることを構造的に
  保証**している。実際に一度も選ばれない確率は数百万行という生成規模では
  実質ゼロ（`eqp_count=400`・`ope_name_pool`100件・`lot_count=6000`の
  既定設定で全400台の使用を確認済み）。
- 「理由コード」（着工遅延の原因）を持つテーブルは今回のスコープに
  含めていない。`proc_history`から得られるのは工程間の待ち時間（着工待ち）
  の大小までで、"なぜ"待たされたかは別テーブルが必要（将来の拡張候補）。
- `docs/reference/`段階のため、このツール自体の正式なユニットテスト
  （`tests/`配下）は未整備。品質担保は生成のたびに自動で走る
  `validate.py`によるルール検証で行う。
