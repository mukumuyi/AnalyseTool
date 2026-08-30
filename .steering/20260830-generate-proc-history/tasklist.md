# tasklist.md — proc_history サンプルデータ生成ツールの新規作成

`design.md`（承認済み）に基づく実装タスク。上から順に進める。

## タスク

- [x] 1. `profiles/proc_history_config.json` を作成する（`ProcHistoryConfig`の
      実体。design.mdに記載のJSON構造・既定値どおり）
- [x] 2. `docs/reference/generate_proc_history/config.py` を実装する
      （`ProcHistoryConfig`・`MinMax`・`LognormalSpec`等のdataclassと
      `load_config()`）
- [x] 3. `docs/reference/generate_proc_history/generate.py` を実装する
      （design.mdの生成ロジック1〜7。品目階層マスタ→設備マスタ（固定処理
      時間）→ルーティング→ロット割当→ロットごとの行生成→`pyarrow.Table`化、
      をそれぞれ独立した純粋関数に分割する）
- [x] 4. `docs/reference/generate_proc_history/validate.py` を実装する
      （`validate_table(table: pa.Table) -> list[str]`。design.mdに記載の
      5つの検証ルールをそれぞれ独立したチェック関数にし、`validate_table()`
      がそれらをまとめて呼ぶ）
- [x] 5. `docs/reference/generate_proc_history/io.py` を実装する
      （設定JSON読込＋Parquetの安全な書き込み：一時ファイルに書いてから
      `os.replace()`でリネーム）
- [x] 6. `docs/reference/generate_proc_history/cli.py` を実装する
      （`--config`必須、`--output`必須、`--seed`既定0、`--lot-count`任意）
- [x] 7. `docs/reference/generate_proc_history/__init__.py`（`main()`）と
      `__main__.py` を実装する（`main()`は
      設定読込→生成→`validate_table()`→違反があれば表示して異常終了→
      問題無ければParquet書き出し、の順で呼ぶ）
- [x] 8. 依存の確認・追加：`uv add --dev ruff mypy pytest`を実行した。
      その際`pyproject.toml`に`[tool.uv] package = false`
      （`docs/architecture.md`に記載済みだが実際には未設定だった）が無いと
      `uv add`自体がビルドエラーで失敗することが判明したため、あわせて
      追加した（既存の技術的制約を実際に反映しただけで、設計変更ではない）
- [x] 9. 動作確認：以下のコマンドで生成が完了し、自動検証（`validate.py`）が
      パスすることを確認した（32,535行）
      ```bash
      PYTHONPATH=docs/reference uv run python -m generate_proc_history \
        --config profiles/proc_history_config.json \
        --output output/proc_history_sample.parquet
      ```
- [x] 10. DuckDBで、自動検証と同じ観点を念のため再確認した（5項目すべて
       違反0件）。あわせて分布の妥当性も確認し、`eqp_processing_minutes`・
       `queue_minutes`の`mean`に「分」の値をそのまま入れていたため
       ほぼ全件が`max`に張り付く不具合を発見・修正した（`mean`は対数正規
       分布の元になる正規分布側のパラメータのため`ln(40)`/`ln(30)`に補正。
       `profiles/proc_history_config.json`・`design.md`に反映済み）
- [x] 11. `docs/reference/generate_proc_history.md`（説明資料）を作成した
       （処理概要・I/O説明・実行オプション・生成ルール・既知の制約）
- [x] 12. 品質チェックを実行した
       - `ruff check` / `ruff format`: 新規モジュールは全てパス
       - `mypy`: 新規モジュール固有の実質的な型エラー（`tuple|None`の
         直接インデックス2件）は修正済み。残るのはpyarrowのpy.typed
         マーカー欠如による警告4件のみで、これは`common/profile.py`や
         既存の`generate_sample_data`にも同種の警告が既にある
         リポジトリ全体の既存課題（変更前から27件）であり、本タスクの
         スコープでは対応しない
       - `pytest`: 0件収集・正常終了（新規ユニットテストはdesign.md記載の
         方針通り追加していない）
- [x] 13. `requirements.md`の受け入れ条件を満たしているか最終確認した
       （下記「最終確認」を参照）

## 最終確認（requirements.mdの受け入れ条件との対応）

- 設定ファイルを読み込みParquetを生成できること → 達成
- 設定ファイルは`DatasetProfile`とは別の専用形式でよい → `ProcHistoryConfig`として実装
- 生成結果が満たすべきデータ特性を全て満たすこと → `validate.py`＋DuckDBでの
  独立確認の両方で違反0件を確認
- 生成規模は数万行程度から開始 → 32,535行
- 対応する説明資料を作成すること → `docs/reference/generate_proc_history.md`
- 制約事項（既存ツールとの相互依存無し／本採用はまだ行わない／永続文書の
  更新は無し）→ いずれも遵守。ただし`pyproject.toml`に`[tool.uv]
  package = false`を追加した（既存の`docs/architecture.md`に記載済みの
  設定が実際には欠けており、`uv add`自体が失敗する状態だったための修正。
  設計判断の変更ではない）

## 完了条件

- 上記タスクが全て完了していること → 完了
- 生成コマンドが正常終了し、`validate.py`の自動検証・DuckDBでの再確認の
  両方でdesign.mdの生成ルールを満たしていること → 確認済み
- `docs/reference/generate_proc_history.md`が作成されていること → 完了
- 新規モジュールについて`ruff check`がエラー無しで通り、`mypy`は
  pyarrowの型スタブ欠如（既存の全参考実装と共通の既知課題）を除き
  エラーが無いこと → 確認済み

## 進捗状況

全タスク完了。
