# tasklist.md — 設備稼働負荷・ロット待機分析ツールの実装タスク

`design.md`（承認済み）に基づく実装タスク。「コンポーネント構成図」の
依存方向（第1層→第2層→案件固有、`common/report.py`は独立）に沿って
上から順に進める。各タスクの完了時に`ruff check`/`mypy`を通す。

## タスク

### 第1層（見た目の型）

- [x] 1. `common/charts/bar.py`に`color`省略時の単色棒モードを追加する
      （既存`stacked_bar()`の引数をオプショナル化。①②③で使用）
- [x] 2. `common/charts/barline.py`を新規実装する（棒＋第2軸の折れ線。
      ⑥-1・⑥-2で共用）
- [x] 3. `common/charts/area.py`を新規実装する（積み上げ面・階段状対応。
      仕掛数量推移の3分類積み上げで使用）
- [x] 4. `common/charts/gantt.py`を新規実装する（区間の水平棒。ロット
      区間は1本の`go.Bar`に配列でまとめる。design.md 5-2節の軽量化策・
      ラベル出し分けを反映）
- [x] 5. `common/charts/scatter.py`を新規実装する（`scattergl`固定。
      ④⑤で使用）
- [x] 6. 上記5モジュールの純粋関数部分にユニットテストを書く
      （`tests/common/charts/`）

### 第2層（分析の型）

- [x] 7. `common/charts/pareto.py`を新規実装する（降順ソート・累積構成比・
      80%目安線の算出は純粋関数として切り出し、描画は`barline.py`に
      委譲）
- [x] 8. `common/charts/twograph.py`を新規実装する（`make_subplots(rows=2,
      cols=1, shared_xaxes=True)`でFigureを作り、`gantt.py`/`area.py`の
      `add_*_traces()`を呼ぶ。単体利用向けの薄いラッパーも用意）
- [x] 9. `twograph.py`のtrace追加順（ガント→仕掛推移）を固定し、
      `curveNumber`でガント側だけを判定できることを、小さいダミー
      データで動作確認する（design.md 6-4節・残課題）

### `common/report.py`の拡張

- [ ] 10. 段構成の設定を受け取り、選択式（段1→2）・構築式（段2→3・
       3→4）の2メカニズムを組み立てる新関数を実装する（既存の1段版
       `build_bar_click_detail_html()`は変更しない）
- [ ] 11. div id命名規則（`stage1-pareto`/`stage2-{eqp_id}`/
       `stage3-gantt`・`stage3-wip`/`stage4-detail`）に沿ったHTML/CSS
       骨格と、表示切り替えの共通JSを実装する
- [ ] 12. `LotDetail`をcolumnar JSON形式で埋め込むヘルパーを実装する
       （records形式ではなく列ごとの配列）

### ツール本体（`trial_factory/eqp_workload_analysis/`）

- [ ] 13. `cli.py`を実装する（`--input`/`--output`/`--profile-output`等。
       `customer_pref_summary`のCLI引数構成を踏襲）
- [ ] 14. `io.py`を実装する（Parquet読み込み、プロファイルJSON書き出し、
       レポートHTML書き出し）
- [ ] 15. `prepare.py`を実装する（`profile_from_parquet()`で傾向を把握。
       レポートには使わず`write_profile()`でJSON書き出しのみ）
- [ ] 16. `process.py`を実装する（`clean_proc_history()`、
       `annotate_lot_sequence()`：`wait_minutes`/`next_eqp_id`/
       `prev_eqp_id`を1回のSELECT文で付与）
- [ ] 17. `process.py`のユニットテストを書く（`annotate_lot_sequence()`の
       境界ケース：ロット最初の工程で`prev_eqp_id`が`NULL`、最後の工程で
       `next_eqp_id`が`NULL`になることを確認）
- [ ] 18. `analyze.py`を実装する（`aggregate_eqp_workload()`・
       `build_pareto()`・`build_hourly_utilization()`・
       `build_lot_records()`。時間帯集計は`generate_series`＋区間交差の
       SQL集合演算で行い、Pythonでロットごとにループしない）
- [ ] 19. `analyze.py`のユニットテストを書く（集計結果の件数・列、
       パレートの累積構成比が100%に収束すること等）
- [ ] 20. `visualize.py`を実装する（①〜⑥-2の`go.Figure`を組み立て、
       `common/report.py`へ渡す。セクションごとに`_build_section*()`の
       小さい関数に分割し、集計・描画ロジックを持ち込まない）
- [ ] 21. ⑥-3・⑥-4のドメイン固有JS（並行処理枠への詰め直し＝貪欲法、
       仕掛数量の3分類集計、ガントのロット区間クリック→明細表更新）を
       `visualize.py`側でJS文字列として組み立て、`report.py`へ渡す
- [ ] 22. `scripts/trial_factory/eqp_workload_analysis.py`を実装する
       （`main()`を呼ぶだけの薄いラッパー）

### 動作確認

- [ ] 23. `uv run python scripts/trial_factory/eqp_workload_analysis.py
       --input data/trial_factory/proc_history.parquet --output
       output/...`を実行し、正常終了することを確認する
- [ ] 24. 生成したレポートHTMLを`file://`で開き、次を目視確認する:
       - ①〜⑤の棒グラフ・散布図が表示される
       - ⑥パレート図クリック→装置稼働グラフ表示（段1→2）
       - 装置稼働グラフの1時間棒クリック→ガント＋仕掛数量推移表示
         （段2→3）。ガント・仕掛推移がズーム・パン連動する
       - ガントの着工中区間クリック→ロット明細表表示（段3→4）
       - 実データでの並行処理枠の行数（想定：平均9・最大16）と、
         「サンプルデータは設備の同時使用制約を持たない」旨の注記表示
- [ ] 25. `prepare.py`が出力するプロファイルJSONを見て、仕掛数量推移の
       3分類（着工中／待機中(自装置)／待機中(他装置)）が極端に偏った
       分布になっていないか確認する（design.md 残課題）

### 説明資料・永続ドキュメント

- [ ] 26. `docs/trial_factory/eqp_workload_analysis.md`を
       `docs/templates/tool-doc.md`から作成する（処理概要・I/O説明・
       実行オプション・既知の制約）
- [ ] 27. `docs/functional-design.md`のコンポーネント表（`common/charts/*`
       の状態）を「未実装（設計合意済み）」→「実装済み」に更新する
- [ ] 28. `docs/functional-design.md`の「ツールごとの実装」表に
       `eqp_workload_analysis`を追加する
- [ ] 29. `docs/repository-structure.md`を更新し、`trial_factory`が
       最初の本採用プロジェクトであることを反映する
- [ ] 30. `docs/product-requirements.md`の「既知のリスク」を見直す
       （design.md「対象」の`DOC`行の通り、`docs/reference/`側の
       プロトタイプが残っている間はリスク文言自体は残す）

### 品質チェック・最終確認

- [ ] 31. `uv run ruff check .` / `uv run ruff format .`を実行する
- [ ] 32. `uv run mypy .`を実行する
- [ ] 33. `uv run pytest`を実行する
- [ ] 34. `requirements.md`の受け入れ条件を満たしているか最終確認する
       （4ステップ構成・DuckDB集計・`file://`自己完結HTML・4段階
       ドリルダウン・並行処理枠の視覚的区別・仕掛数量推移の3分類・
       説明資料の作成・品質チェック通過）

## 完了条件

- 上記タスクがすべて完了していること
- 生成コマンドが正常終了し、動作確認（タスク23〜25）で問題が
  無いこと
- `docs/trial_factory/eqp_workload_analysis.md`が作成されていること
- `ruff check`/`mypy`がエラー無しで通り、`pytest`が全て通ること

## 進捗状況

第1層（タスク1〜6）完了。実装にあたり、本ツールが本リポジトリ初の
「本採用」であるため`pyproject.toml`の`[tool.uv] package = false`を解除
（`docs/architecture.md`の記載通り）し、`analyse_tool`を実際にimport可能な
パッケージとしてビルドされるようにした。あわせて`pandas`の型スタブ
（`pandas-stubs`）を開発依存に追加し、`plotly`/`duckdb`（型スタブ未配布）は
`pyproject.toml`の`[[tool.mypy.overrides]]`でimportエラーのみ無視するよう
設定した（本ツールで初めて`mypy`が`src/`配下の実コードを型チェックする
ため、リポジトリ共通の設定として一度だけ必要になったもの）。

第2層（タスク7〜9）完了。`twograph.py`のユニットテストで、ダミーデータ
でも`gantt.add_gantt_traces()`が常に`fig.data[0]`（`curveNumber == 0`）に
なることを確認した（残課題としていた動作確認を、実ブラウザではなく
ユニットテストで自動化）。
