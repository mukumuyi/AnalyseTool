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
7. 全ロットぶんの行をまとめて`pyarrow.Table`にし、生成結果を検証してから
   Parquetへ書き出す（検証は次項「生成結果の自動検証」を参照）

行数が数万件規模（`lot_count`×平均工程数）を想定しており、
`generate_sample_data`のようなチャンク分割書き出しは不要。一度に
`pyarrow.Table`を組み立ててから1回で書き出す。書き出しは
`docs/development-guidelines.md`の「出力ファイルの安全な書き込み」に従い、
一時ファイルに書いてから成功時のみ`os.replace()`でリネームする（既存の
`generate_sample_data`参考実装はこの規約に沿っていないが、今回は新規実装
として規約を満たす）。

## 生成結果の自動検証（レビュー指摘反映: 新規追加）

DuckDBで人手で確認するだけでなく、**生成ロジック自身が決まったルールを
守っているかをその場で自動検証する**ステップを`validate.py`に実装し、
`main()`が生成直後・書き出し前に必ず呼び出す。違反があれば理由を明示して
異常終了させ（Parquetは書き出さない）、壊れたデータに気づかないまま出力
してしまう事態を防ぐ。

検証する主なルール（＝これまで合意してきた生成ルールそのもの）：

- 全行で`start_time < end_time`が成り立つ
- ロットごとに`ope_seq`が1から欠番なく連番になっている
- 同一ロット内で、工程`N+1`の`start_time`が工程`N`の`end_time`より
  必ず後ろになっている（同時刻・逆転がない）
- 同じ`eqp_id`を使った行はすべて`end_time - start_time`が同一の固定値に
  なっている（設備ごとの処理時間が本当に一定か）
- `mainpd_id`は常に同じ`prodspec_id`に紐づいている（階層の矛盾がない）

`validate.py`は`def validate_table(table: pa.Table) -> list[str]`という
「`pyarrow.Table`を受け取り、違反内容の説明文リストを返す（空なら問題無し）」
純粋関数として実装する。`__init__.py`の`main()`は、このリストが空でなければ
違反内容を全て表示して`SystemExit`で異常終了する。

## 変更するコンポーネント（新規作成のみ、既存ファイルの変更は無し）

**モジュール構成（レビュー指摘反映: 1ディレクトリに集約）**: 既存の
`generate_sample_data`は「トップレベルのエントリスクリプト」＋
「`analyse_tool/`配下に分散したパッケージ」の2箇所に分かれているが、
今回は`docs/reference/`直下にこのツール専用の1ディレクトリを作り、
エントリポイントを含めて中身をすべてそこにまとめる。

```text
docs/reference/
├── generate_proc_history/              # このツール一式をここに集約
│   ├── __init__.py                     # main()：config読込→生成→検証→書き出し
│   ├── __main__.py                     # `python -m generate_proc_history`用
│   ├── cli.py                          # 引数定義（--config/--output/--seed/--lot-count）
│   ├── config.py                       # ProcHistoryConfig（設定JSONのデータ構造・読込）
│   ├── io.py                           # 設定読込・Parquet安全書き込み
│   ├── generate.py                     # 生成ロジック本体（上記1〜7の純粋関数群）
│   └── validate.py                     # 生成結果の検証（上記「生成結果の自動検証」）
└── generate_proc_history.md            # 説明資料（処理概要/IO/実行オプション。既存の
                                         # `generate_sample_data.md`と同じ並びに置く）

profiles/
└── proc_history_config.json            # ProcHistoryConfigの実体（後述）
```

実行は`PYTHONPATH=docs/reference uv run python -m generate_proc_history
--config ... --output ...`とする（`analyse_tool`パッケージには一切触れず、
`generate_sample_data`との依存も発生しない）。

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
  "ope_name_pool": ["受入一", "受入二", "...(100件)"],
  "steps_per_routing": { "min": 600, "max": 800 },
  "eqp_count": 400,
  "eqp_per_ope_name": { "min": 6, "max": 10 },
  "eqp_processing_minutes": { "distribution": "lognormal", "mean": 3.6889, "stddev": 0.25, "min": 10, "max": 120 },
  "queue_minutes": { "distribution": "lognormal", "mean": 3.4012, "stddev": 1.0, "min": 1, "max": 4320 },
  "lot_count": 5000,
  "time_range": { "start": "2026-01-01T00:00:00", "end": "2026-06-30T23:59:59" }
}
```

- `mean`/`stddev`は`common/profile.py`の`lognormal`と同じ扱い（対数正規分布の
  元になる正規分布側のパラメータ）とし、`min`/`max`でクリップする。
  例えば`eqp_processing_minutes`を「平均40分程度」にしたい場合は
  `mean`に`ln(40)≈3.6889`を設定する（`40`をそのまま入れると`exp(40)`
  相当の桁になり、ほぼ全ての値が`max`に張り付いてしまう。実装時に
  この点を実際に検証し、上記の値に補正した）。
- `seed`は`DatasetProfile`同様に設定ファイルへ持たせず、`generate_sample_data`
  に揃えて**CLI引数`--seed`（既定0）**でのみ指定する。
- `lot_count`は`generate_sample_data`の`--rows`に相当するものとして、
  CLI引数`--lot-count`で上書き可能にする（省略時は設定ファイルの値を使う）。
- **`eqp_per_ope_name`は当初固定の整数だったが、実装後のユーザー指示により
  `{min, max}`のレンジに変更した**（`ope_no`ごとに個別に候補台数を決める）。
  `config.py`の型を`int`→`MinMax`に、`generate.py`の
  `_build_ope_eqp_candidates()`を「`ope_no`ごとに範囲内で個別に台数を
  引く」実装に修正済み。
- `ope_name_pool`は実際のデータ規模検証のため100件に拡張した
  （`steps_per_routing`も600〜800に拡張。プール件数よりステップ数の方が
  大きいため、同じ`ope_no`を繰り返し使うルーティングになる＝
  `_build_routing()`の`replace=True`分岐がここで実際に使われる）。

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
  未作成）。今回もこの前例を踏襲し、`docs/reference/`段階では正式な
  pytestは追加しない。代わりに、生成のたびに自動で走る`validate.py`
  （上記「生成結果の自動検証」）を品質担保の主手段とする。これは
  「テストの代わり」ではなく「生成ロジック自体の一部」という位置づけで、
  `src/`への本採用時には`validate.py`のロジックをベースに正式な
  ユニットテストへ引き上げる（`docs/product-requirements.md`の
  「既知のリスク」に記載されている、参考実装と本採用の乖離リスクと同種の
  扱いとする）。
- **依存パッケージ**: 追加は不要（`numpy`/`pyarrow`は`pyproject.toml`に
  既存）。

## 検証方法（実装後に実施）

1. 生成コマンドが完了し、`validate.py`による自動検証もパスすること
   ```bash
   PYTHONPATH=docs/reference uv run python -m generate_proc_history \
     --config profiles/proc_history_config.json \
     --output output/proc_history_sample.parquet
   ```
2. 念のためDuckDBでも以下を確認する（自動検証と同じ観点の再確認）
   - 総行数が`lot_count`×平均工程数に近いこと
   - ロットごとに`ope_seq`が1から連番で欠番なく並んでいること
   - 同一ロット内で工程`N+1`の`start_time`が工程`N`の`end_time`より
     常に後ろになっていること（同時刻・逆転がないこと）
   - 同じ`eqp_id`を使った行はどれも`end_time - start_time`が同一の固定値に
     なっていること
   - `mainpd_id`が常に想定した`prodspec_id`の子として一貫していること
