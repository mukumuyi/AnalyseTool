# tasklist.md — proc_history サンプルデータ生成ツールの新規作成

`design.md`（承認済み）に基づく実装タスク。上から順に進める。

## タスク

- [ ] 1. `profiles/proc_history_config.json` を作成する（`ProcHistoryConfig`の
      実体。design.mdに記載のJSON構造・既定値どおり）
- [ ] 2. `docs/reference/generate_proc_history/config.py` を実装する
      （`ProcHistoryConfig`・`MinMax`・`LognormalSpec`等のdataclassと
      `load_config()`）
- [ ] 3. `docs/reference/generate_proc_history/generate.py` を実装する
      （design.mdの生成ロジック1〜7。品目階層マスタ→設備マスタ（固定処理
      時間）→ルーティング→ロット割当→ロットごとの行生成→`pyarrow.Table`化、
      をそれぞれ独立した純粋関数に分割する）
- [ ] 4. `docs/reference/generate_proc_history/validate.py` を実装する
      （`validate_table(table: pa.Table) -> list[str]`。design.mdに記載の
      5つの検証ルールをそれぞれ独立したチェック関数にし、`validate_table()`
      がそれらをまとめて呼ぶ）
- [ ] 5. `docs/reference/generate_proc_history/io.py` を実装する
      （設定JSON読込＋Parquetの安全な書き込み：一時ファイルに書いてから
      `os.replace()`でリネーム）
- [ ] 6. `docs/reference/generate_proc_history/cli.py` を実装する
      （`--config`必須、`--output`必須、`--seed`既定0、`--lot-count`任意）
- [ ] 7. `docs/reference/generate_proc_history/__init__.py`（`main()`）と
      `__main__.py` を実装する（`main()`は
      設定読込→生成→`validate_table()`→違反があれば表示して異常終了→
      問題無ければParquet書き出し、の順で呼ぶ）
- [ ] 8. 依存の確認・追加：`uv run ruff check .`・`uv run mypy .`・
      `uv run pytest`が未導入なら`uv add --dev ruff mypy pytest`を実行する
      （`docs/development-guidelines.md`の規約に必要な開発依存。現状の
      `pyproject.toml`にはまだ入っていない）
- [ ] 9. 動作確認：以下のコマンドで生成が完了し、自動検証（`validate.py`）が
      パスすることを確認する
      ```bash
      PYTHONPATH=docs/reference uv run python -m generate_proc_history \
        --config profiles/proc_history_config.json \
        --output output/proc_history_sample.parquet
      ```
- [ ] 10. DuckDBで、自動検証と同じ観点を念のため再確認する（design.mdの
       「検証方法」記載の5項目：総行数感、`ope_seq`の連番、時系列の単調
       増加、設備ごとの処理時間の固定、`mainpd_id`/`prodspec_id`の階層一貫性）
- [ ] 11. `docs/reference/generate_proc_history.md`（説明資料）を作成する
       （処理概要・I/O説明・実行オプション。既存の
       `docs/reference/generate_sample_data.md`の構成に揃える）
- [ ] 12. 品質チェックを実行し、問題が無いことを確認する
       ```bash
       uv run ruff check .
       uv run ruff format .
       uv run mypy .
       uv run pytest
       ```
       （`docs/reference/`段階のためこのツール自体の新規ユニットテストは
       追加しない方針＝design.md記載。`pytest`はリポジトリ全体に既存の
       テストが無ければ0件成功として扱う）
- [ ] 13. `requirements.md`の受け入れ条件を満たしているか最終確認する

## 完了条件

- 上記タスクが全て完了していること
- `PYTHONPATH=docs/reference uv run python -m generate_proc_history --config profiles/proc_history_config.json --output output/proc_history_sample.parquet`
  が正常終了し、`validate.py`の自動検証・DuckDBでの再確認の両方で
  design.mdの生成ルールを満たしていることが確認できていること
- `docs/reference/generate_proc_history.md`が作成されていること
- `uv run ruff check .` / `uv run mypy .`がエラー無しで通ること

## 進捗状況

未着手（承認待ち）。承認後、上から順にタスクを実施し、完了したチェック
ボックスを都度更新する。
