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

- [x] 10. 段構成の設定を受け取り、選択式（段1→2）・構築式（段2→3・
       3→4）の2メカニズムを組み立てる新関数を実装する（既存の1段版
       `build_bar_click_detail_html()`は変更しない）
- [x] 11. div id命名規則に沿ったHTML/CSS骨格と、表示切り替えの共通JSを
       実装する（`stage3-gantt`・`stage3-wip`を2つの独立したdivに分ける
       案は、design.mdが確定させた「twograph.pyのsubplot構成は1段1Figure」
       という技術決定と矛盾するため、実装時に`stage3-chart`という単一の
       div（1つの`go.Figure`、上下2段のsubplot）に統一した）
- [x] 12. `LotDetail`をcolumnar JSON形式で埋め込むヘルパーを実装する
       （records形式ではなく列ごとの配列）

### ツール本体（`trial_factory/eqp_workload_analysis/`）

- [x] 13. `cli.py`を実装する（`--input`/`--output-dir`/`--top-n`/
       `--period-days`/`--gantt-window-hours`）
- [x] 14. `io.py`を実装する（Parquet読み込み、プロファイルJSON書き出し、
       レポートHTML書き出し＋`output/index.html`への登録）
- [x] 15. `prepare.py`を実装する（`profile_from_parquet()`で傾向を把握。
       レポートには使わず`write_profile()`でJSON書き出しのみ）
- [x] 16. `process.py`を実装する（`clean_proc_history()`、
       `annotate_lot_sequence()`：`wait_minutes`/`next_eqp_id`/
       `prev_eqp_id`を1回のSELECT文で付与）
- [x] 17. `process.py`のユニットテストを書く（`annotate_lot_sequence()`の
       境界ケース：ロット最初の工程で`prev_eqp_id`が`NULL`、最後の工程で
       `next_eqp_id`が`NULL`になることを確認）
- [x] 18. `analyze.py`を実装する（`aggregate_eqp_workload()`・
       `build_pareto()`・`build_hourly_utilization()`・
       `build_lot_records()`。時間帯集計は`generate_series`＋区間交差の
       SQL集合演算で行い、Pythonでロットごとにループしない）
- [x] 19. `analyze.py`のユニットテストを書く（集計結果の件数・列、
       パレートの累積構成比が100%に収束すること等）
- [x] 20. `visualize.py`を実装する（①〜⑥-2の`go.Figure`を組み立て、
       `common/report.py`へ渡す。セクションごとに`_build_section*()`の
       小さい関数に分割し、集計・描画ロジックを持ち込まない）
- [x] 21. ⑥-3・⑥-4のドメイン固有JS（並行処理枠への詰め直し＝貪欲法、
       仕掛数量の3分類集計、ガントのロット区間クリック→明細表更新）を
       `visualize.py`側でJS文字列として組み立て、`report.py`へ渡す。
       段3の初期表示も含め、段3のすべての表示をこのJSの1経路に統一し
       （Python側では空のプレースホルダFigureのみ用意）、貪欲法・3分類
       判定のロジックをPython/JSの2箇所に重複実装しない設計にした
- [x] 22. `scripts/trial_factory/eqp_workload_analysis.py`を実装する
       （`main()`を呼ぶだけの薄いラッパー）

### 動作確認

- [x] 23. `uv run python scripts/trial_factory/eqp_workload_analysis.py
       --input data/trial_factory/proc_history.parquet --output-dir
       output`を実行し、正常終了することを確認した
       （4,211,253行→レポート約500KB、数秒で完了）
- [x] 24. 生成したレポートHTMLを、ヘッドレスブラウザ（Playwright+
       Chromium）で実際にクリックを発火させて動作確認した
       （`file://`はplotly.jsをCDNから読み込む構成のため、サンドボックス
       内の検証ではplotly.js本体をローカルファイルに差し替えたコピーで
       確認し、実ファイル自体はCDN読み込みのまま変更していない）:
       - ①〜⑤の棒グラフ・散布図が表示される
       - ⑥パレート図クリック→装置稼働グラフ表示（段1→2）
       - 装置稼働グラフの1時間棒クリック→ガント＋仕掛数量推移表示
         （段2→3）。`shared_xaxes`でズーム・パン連動する軸構成を確認
       - ガントの着工中区間クリック→ロット明細表表示（段3→4）。
         待機区間（`lot_id`なし）をクリックしても何も起きないことも確認
       - この検証を通じて実装上のバグを3件発見・修正した（詳細は下記
         「進捗状況」）。並行処理枠の行数は、上位15台（待機時間合計基準）
         ×代表期間3日間×任意の4時間窓をスイープした実測で最大3行
         だった（設計時に見積もった「平均9・最大16」は全設備・全期間を
         対象にした無絞り込みのスイープライン集計によるもので、母集団が
         異なるため直接比較はできない。可変行数・スクロール前提の実装
         自体は妥当で、実測3行はその範囲内に収まっている）
- [x] 25. 生成したレポートで仕掛数量推移の3分類を確認した。1つの
       ガント窓の実例で着工中/待機中(自装置)/待機中(他装置)の3分類が
       いずれも0でない値を持つことを確認した（極端な偏りは無い）

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

- [x] 31. `uv run ruff check .` / `uv run ruff format .`を実行する
      （`pyproject.toml`に`[tool.ruff.lint] ignore = ["DTZ"]`を追加。
      本ツールはローカル単一ユーザー実行前提で、`output/`のファイル名・
      目次に使う実行日時はUTCではなくローカル時刻であるべきため）
- [x] 32. `uv run mypy .`を実行する
- [x] 33. `uv run pytest`を実行する（52件、全て成功）
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

タスク10〜25完了。`common/report.py`拡張・ツール本体・動作確認まで一括で
実装し、実データ（`data/trial_factory/proc_history.parquet`、
4,211,253行）に対して実行・ヘッドレスブラウザでの動作確認まで行った。

動作確認（タスク24）の過程で、実装上のバグを3件発見し修正した
（いずれもユニットテストの回帰テストを追加済み）:

1. `analyze.py`の`build_hourly_utilization()`で、着工件数(`start_count`)
   の集計が`date_trunc('hour', start_time)`で時間帯を求めていたが、
   代表期間の開始時刻（実データの`MIN(start_time)`）は0分0秒起点で
   ないため、時間帯の境界と噛み合わず常に0件になっていた。`hours`と
   同じ半開区間の条件で結合するよう修正した。
2. 同じく`build_hourly_utilization()`で、稼働分数(`busy_minutes`)の
   算出に使っていた`LEFT JOIN`が、DuckDBの`GREATEST`/`LEAST`が
   `NULL`引数を無視する仕様と組み合わさり、「重なる行が無い時間帯」を
   満稼働（60分）と誤集計していた。`INNER JOIN`に変更し、該当行が
   無い時間帯は素直に0分として扱うようにした。
3. ガントチャートの区間が実際の時刻位置に描かれず、常に`x=0`起点で
   結合されて表示される不具合があった。原因は2つ: (a) `go.Bar`の
   `base`（区間の開始時刻）にJavaScriptの`Date`オブジェクトをそのまま
   渡すとPlotly.jsが正しく解釈しない（ISO文字列に変換する必要がある）、
   (b) `base`が日時でも`x`（所要時間）が数値のため、x軸の型が自動判定で
   日時軸と認識されない（明示的に`type: "date"`を指定する必要がある）。
   この(b)は`common/charts/gantt.py`（Python側）にも同じ潜在バグが
   あったため、`add_gantt_traces()`内で明示的に`fig.update_xaxes(
   type="date")`するよう修正した（両方に回帰テストを追加）。
   あわせて、`twograph.py`の`gantt_and_wip_chart()`に残っていた
   `barmode="stack"`も、ガント側の複数区間（同じ行を共有する複数の
   `base`位置）を誤って累積的に積み上げてしまう副作用があったため削除した。

また、代表期間には稼働がほぼ無い時間帯も多いこと（実測: 着工中の
分数が0の時間帯が72%）が分かったため、段3の初期表示（ページを開いた
直後にドメインJSが自動描画する既定の設備・時間帯）は、単純に代表期間の
先頭ではなく、最も稼働している時間帯を選ぶよう`visualize.py`の
`_default_hour()`で調整した。
