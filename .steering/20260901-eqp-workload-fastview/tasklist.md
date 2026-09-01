# tasklist.md — 新規ツール `eqp_workload_fastview`（1ヶ月/1日表示・高速モード）

進捗記号: `[ ]` 未着手 / `[~]` 着手中 / `[x]` 完了

`eqp_workload_analysis`（旧版）のファイルは対象外。以下はすべて
`trial_factory/eqp_workload_fastview/`配下の新規実装。

## タスク一覧

### 0. サブパッケージの雛形作成
- [x] 0-1. `src/analyse_tool/trial_factory/eqp_workload_fastview/`（`__init__.py`含む）作成
- [x] 0-2. `scripts/trial_factory/eqp_workload_fastview.py`（薄いエントリポイント）作成
- [x] 0-3. `tests/trial_factory/eqp_workload_fastview/`作成

### 1. `prepare.py` / `process.py` — EDA・前処理（旧版と同等の内容を複製実装）
- [x] 1-1. `prepare.py`：`common/profile.py`の`profile_from_parquet()`を呼ぶEDA
- [x] 1-2. `process.py`：必須列チェック・`wait_minutes`/`prev_eqp_id`/`next_eqp_id`付与
- [x] 1-3. ユニットテスト（旧版の`test_process.py`相当のケースを踏襲）

### 2. `analyze.py` — ①〜⑤/⑥-1集計＋⑥-2/⑥-3/⑥-4用の日次・日別処理
- [x] 2-1. ①〜⑤/⑥-1用の集計（旧版`aggregate_eqp_workload`/`build_pareto`相当を複製）
- [x] 2-2. ⑥-2用`aggregate_daily_index()`（対象設備群×日の稼働率・着工件数、DuckDB集計）
- [x] 2-3. ⑥-3用`build_day_segments()`（対象日・対象設備群の区間抽出＋当日境界クリップ）
- [x] 2-4. `assign_sublanes()`（区間リスト→レーン番号リスト、貪欲法の純粋関数）
- [x] 2-5. `build_day_wip_series()`（15分刻み・3分類の仕掛数量、当日分）
- [x] 2-6. `build_day_lot_detail()`（当日ガントに登場するロットのグループ内工程明細、`boundary_buffer_days=1`）
- [x] 2-7. ユニットテスト（2-1〜2-6、境界値・空データ・重複区間ケースを含む）

### 3. `io.py` — ディレクトリ出力・安全書き込み
- [x] 3-1. 出力ディレクトリ構成（`index.html`＋`data/daily_index.json`＋`data/days/<日付>.json`）への書き出し実装
- [x] 3-2. 一時ファイル→`os.replace()`の安全書き込み
- [x] 3-3. `register_output()`呼び出し（`output/trial_factory/index.html`への登録）
- [x] 3-4. `tmp_path`を使った結合テスト（生成ディレクトリの構造・JSONの妥当性を検証）

### 4. `fast_client.py`（新規） — ブラウザ側JS
- [x] 4-1. 日クリック→`data/days/<日付>.json`を`fetch()`するJS
- [x] 4-2. Canvas 2Dで設備×サブレーンの矩形を描画するJS（画面外は描画しない）
- [x] 4-3. ホバーで装置ID・開始・終了を表示するツールチップJS（ロット名は出さない）
- [x] 4-4. 着工中区間クリック→⑥-4テーブル更新JS
- [x] 4-5. 生成したJS文字列に想定キー（fetch先パス、canvas要素id等）が含まれることを検証するテスト

### 5. `visualize.py` — レポート組み立て
- [x] 5-1. ①〜⑤（棒グラフ／散布図）を`common/charts/bar.py`・`scatter.py`で組み立て
- [x] 5-2. ①〜⑤・⑥-1を`<details>`アコーディオンで包む（①〜⑤は初期閉、⑥-1は初期開）
- [x] 5-3. ⑥-1パレート図を`common/charts/pareto.py`で組み立て（非クリック・静的表示）
- [x] 5-4. ⑥-2を全期間日次データ・`barline.py`で組み立て、日クリックが`fast_client.py`のfetch処理を呼ぶよう配線
- [x] 5-5. ⑥-3（Canvas＋ホバー）・⑥-4（テーブル）のシェルHTML組み立て
- [x] 5-6. `--single-file`向け：初期表示日（稼働最多日）1日分の⑥-3/⑥-4データを静的埋め込みし、他日切替不可の注記を出す

### 6. `server.py`（新規） — ローカル静的サーバー
- [x] 6-1. `serve(directory, port=0)`（`http.server.ThreadingHTTPServer`、標準ライブラリのみ）
- [x] 6-2. 起動後にURLを標準出力へ表示
- [x] 6-3. `index.html`が存在しないディレクトリを指定した場合のエラーメッセージ
- [x] 6-4. テスト（起動→HTTP GETで`index.html`が取得できることを確認→終了）

### 7. `cli.py` / `__init__.py` — 起動オプション配線
- [x] 7-1. `--input`／`--output-dir`／`--top-n`（旧版と同じ既定値・意味）
- [x] 7-2. `--period-days`（既定値は全期間相当）
- [x] 7-3. `--serve`（生成後に高速モードで起動）／`--single-file`（フォールバック出力のみ）フラグ
- [x] 7-4. `main()`で4ステップ呼び出し＋`--serve`指定時のみ`server.serve()`を呼ぶよう配線
- [x] 7-5. CLIの結合テスト

### 8. 性能実測
- [x] 8-1. `proc_history_sample.parquet`相当でのデータ生成時間を計測
- [x] 8-2. 日付切替2回目以降・ロット選択→⑥-4更新を`performance.now()`で計測し、中央値・95パーセンタイルを記録（ズーム/スクロールは⑥-3に実装していないため対象外。「実施結果」参照）
- [x] 8-3. 初回日付選択（ファイルI/O含む）の95パーセンタイルを記録
- [x] 8-4. 高速モード初回起動（URLアクセス→⑥-2操作可能）を計測
- [x] 8-5. 受け入れ条件の目標値（100ms/300ms/2秒）と比較し、未達の場合は原因切り分け・対応

### 9. ドキュメント更新
- [x] 9-1. `docs/trial_factory/eqp_workload_fastview.md`を新規作成（`docs/templates/tool-doc.md`を複製）
- [x] 9-2. `docs/product-requirements.md`に`eqp_workload_fastview`限定の自己完結HTML例外を明記
- [x] 9-3. `docs/architecture.md`にローカル静的サーバー配信パターンを追記

### 10. 品質チェック・最終確認
- [x] 10-1. `uv run ruff check .` / `uv run ruff format .`
- [x] 10-2. `uv run mypy .`
- [x] 10-3. `uv run pytest`（新規テストがすべて成功。既存テストも成功すること）
- [x] 10-4. `git diff` で`trial_factory/eqp_workload_analysis/`配下・
  `docs/trial_factory/eqp_workload_analysis.md`に差分が無いことを確認
- [x] 10-5. requirements.mdの受け入れ条件（性能／表示・操作／品質）を1件ずつ突き合わせて確認

### 11. ⑥-3ズーム・スクロール追加（2026-09-01 最終報告後にユーザー指示で追加）
- [x] 11-1. `fast_client.py`：表示範囲状態（`viewStart`/`viewEnd`）と
  座標変換をホイールズーム・ドラッグパンに対応させる（画面外の区間は
  描画・ヒットテストをスキップ）
- [x] 11-2. `fast_client.py`：目盛（axis）を表示範囲に応じて動的生成する
  `renderAxis()`を追加
- [x] 11-3. `visualize.py`：`_build_axis_ticks_html()`を削除し、
  `.gantt-axis`の初期HTMLをJS側の`renderAxis()`呼び出しに一本化
- [x] 11-4. ダブルクリックで全期間表示へリセットする処理を追加
- [x] 11-5. 日切替時（`selectDay`）にズーム・パン状態をリセットする処理を追加
- [x] 11-6. `test_fast_client.py`にズーム・パン・リセット関連の識別子検証テストを追加
- [x] 11-7. Playwrightでの動作確認（ホイールズーム・ドラッグパン・
  ダブルクリックリセット・ズーム後のホバー/クリックが正しく機能すること）
- [x] 11-8. ズーム・パン操作の性能実測（100ms目標との比較）
- [x] 11-9. `ruff check`／`ruff format`／`mypy`／`pytest`（全体）の再実行
- [x] 11-10. `docs/trial_factory/eqp_workload_fastview.md`にズーム・スクロール操作の説明を追記

### 12. ⑥-3ズーム・パンと仕掛数量推移(WIP)グラフの同期（2026-09-02 ユーザー指示で追加）
- [x] 12-1. `fast_client.py`：`renderWip()`のX軸を固定`/1440`から
  現在の表示範囲（`viewStart`/`viewEnd`）基準へ変更（Y軸は1日全体の
  最大値で固定し非同期のまま）
- [x] 12-2. `fast_client.py`：`zoomAt()`・ドラッグパンの`mousemove`
  ハンドラ・ダブルクリックリセットの各所で`renderWip()`も呼ぶよう配線
- [x] 12-3. `fast_client.py`：WIPグラフにもガントと同じ目盛線を描画
- [x] 12-4. `visualize.py`：`.wip-body-row`（`140px 1fr`グリッド）を
  導入し、WIPのcanvasがガントのcanvasと横方向のピクセル位置で揃うように修正
- [x] 12-5. `requirements.md`・`design.md`の「WIPグラフはズーム対象外」
  という記述を撤回・改訂
- [x] 12-6. `test_fast_client.py`にWIP同期の配線を検証するテストを追加
- [x] 12-7. Playwrightでの動作確認（WIPのcanvas位置整列、ズーム・パン・
  リセットでWIPも連動して再描画されること）
- [x] 12-8. ズーム・パン操作の性能再計測（WIP再描画を含めても100ms目標内か）
- [x] 12-9. `ruff check`／`ruff format`／`mypy`／`pytest`（全体）の再実行
- [x] 12-10. `docs/trial_factory/eqp_workload_fastview.md`の記載をWIP同期に合わせて更新

### 13. ⑥-3縦寸法縮小・装置ステータス背景・WIP軸目盛・待機二重計上修正（2026-09-02 ユーザー指示で追加）
- [x] 13-1. `fast_client.py`：`ROW_HEIGHT_PX`/`ROW_GAP_PX`/`EQP_GAP_PX`を
  1/4程度に縮小、設備ラベルをID表示のみ（サブレーン数はホバー`title`）に簡略化
- [x] 13-2. `fast_client.py`：`mergeIntervals()`と装置ステータス背景
  （稼働中/待機中）の描画を追加（区間バーより先に描画）
- [x] 13-3. `visualize.py`：装置ステータス背景色の定数追加・凡例追加
- [x] 13-4. `fast_client.py`／`visualize.py`：仕掛数量推移グラフに
  Y軸目盛（`#wip-axis`、0・中間・最大値）を追加
- [x] 13-5. `analyze.py`：`build_day_wip_series()`の`wait_other`
  二重計上バグを修正（対象設備群内での移動を除外）
- [x] 13-6. `test_analyze.py`に二重計上の回帰テストを追加
- [x] 13-7. `test_fast_client.py`にステータス背景・WIP軸のテストを追加
- [x] 13-8. `ruff check`／`ruff format`／`mypy`／`pytest`（全体）の再実行
- [x] 13-9. Playwrightでの動作確認（背景色の表示・凡例、WIP軸ラベル、
  実データでの二重計上解消）
- [x] 13-10. `docs/trial_factory/eqp_workload_fastview.md`の更新
  （※実施結果に記載のとおり、実際にはタスク14と同時に反映した）

### 14. 仕掛数量推移の待機中カテゴリ統合（2026-09-02 ユーザー指示で追加）
- [x] 14-1. `analyze.py`：`build_day_wip_series()`の戻り列を
  `busy`/`wait_self`/`wait_other`から`busy`/`wait`へ統合
- [x] 14-2. `visualize.py`：`build_day_payload()`の`wip`辞書・
  `COLOR_WAIT_SELF`/`COLOR_WAIT_OTHER`定数・凡例・タイトル文言を
  2分類（着工中/待機中）に合わせて整理
- [x] 14-3. `fast_client.py`：`renderWip()`を2バンド積み上げへ簡略化、
  未使用になった配色パラメータを削除
- [x] 14-4. `test_analyze.py`／`test_visualize.py`／`test_fast_client.py`
  の関連テストを更新
- [x] 14-5. `requirements.md`・`design.md`の該当受け入れ条件・記述を改訂
- [x] 14-6. `ruff check`／`ruff format`／`mypy`／`pytest`（全体）の再実行
- [x] 14-7. Playwrightでの動作確認（2バンド積み上げの表示・実データでの
  合計値確認）
- [x] 14-8. `docs/trial_factory/eqp_workload_fastview.md`の更新
  （タスク13分とあわせて反映）

## 完了条件

- 上記タスクがすべて完了し、10-5でrequirements.mdの受け入れ条件を満たしていること。
- `ruff check`／`ruff format`／`mypy`／`pytest`が成功していること。
- `docs/trial_factory/eqp_workload_fastview.md`が新規作成されていること。
- 旧版`eqp_workload_analysis`に一切差分が無いこと。

## 次回以降への申し送り事項

- ⑥-1パレート図クリックで該当設備の⑥-3行へスクロールする等の代替導線は、
  今回のスコープ外とした（design.mdの「課題対応」参照）。
- `process.py`・①〜⑤/⑥-1の集計ロジックは旧版と重複したまま複製実装した。
  3つ目のツールが同じロジックを必要にした時点で
  `trial_factory/common/`への切り出しを検討する。
- 高速モードを使うツールが2つ目に現れた時点で、`server.py`の起動処理と
  `assign_sublanes()`の`src/analyse_tool/common/`への切り出しを検討する
  （1ツールのみの現段階では見送り）。
- ローカルサーバーの`--port`固定オプションの要否は未確認（design.mdの
  「残課題」参照。今回はOS自動割当のみ実装）。
- ~~requirements.mdの性能受け入れ条件「ズーム・スクロール」の操作性能
  計測対象が⑥-3に未実装~~ → **解決済み**。ユーザー指示によりマウス
  ホイール（ズーム）＋ドラッグ（パン）＋ダブルクリック（リセット）を
  追加実装し、Playwrightでの動作確認・性能実測（100ms目標を大きく
  上回って達成）まで完了した。詳細は「タスク11」参照。
- 高速モード初回起動（8-4）の2秒目標について、本開発サンドボックス環境
  では中央値約2.2秒・95パーセンタイル約2.8秒で未達だった。原因切り分け
  の結果、ボトルネックはfastview固有の実装ではなくPlotly本体（①〜⑤・
  ⑥-1・⑥-2が使用、design.mdで「既存のPlotlyを継続する」と決定済み）の
  CDN読込・JS解析コストであることを確認した（詳細は「実施結果」参照）。
  design.mdの決定を覆す設計変更は今回のスコープ外としたため、次回以降
  で次の2点を確認したい。(1) 代表的な開発PC（本サンドボックス以外）
  での再計測。(2) 再計測でも恒常的に2秒を超える場合のPlotly依存軽量化
  （自己ホスト・軽量ビルド選定・①〜⑤の遅延描画等）の要否。
- ~~`uv run mypy .`（プロジェクト全体）が既存の問題で失敗する~~
  → **解決済み**。ユーザー承認のうえ`docs/reference/analyse_tool/`
  （`customer_pref_summary`・`generate_sample_data`を含む）と
  `docs/reference/customer_pref_summary.{py,md}`・
  `docs/reference/generate_sample_data.{py,md}`を削除し、あわせて
  `pyproject.toml`に`[tool.pytest.ini_options] addopts =
  "--import-mode=importlib"`（テストファイル名衝突対策。これに伴い
  `tests/trial_factory/eqp_workload_fastview/__init__.py`は不要になり
  削除）・`[tool.mypy] explicit_package_bases = true` / `mypy_path =
  "src"`（同じ衝突のmypy側対策）・`pyarrow.*`の
  `ignore_missing_imports`（`docs/reference/generate_proc_history/`が
  pyarrowを直接importするため）を追加した。この結果`ruff check .`／
  `ruff format --check .`／`mypy .`／`pytest`（88件）がすべてプロジェクト
  全体で成功する状態になった（詳細は「実施結果」の追記参照）。

## 実施結果

### タスク0〜7（サブパッケージ実装）

前回セッション（VSCodeクラッシュにより中断）で実装済みだった`prepare.py`
`process.py``analyze.py``io.py``fast_client.py``visualize.py``server.py`
`cli.py`および対応するユニットテスト一式について、本セッションで内容を
1ファイルずつ確認し、design.md・requirements.mdの記載と突き合わせて
相違が無いことを確認した（旧版`eqp_workload_analysis`との既定値の一致、
`register_output()`シグネチャとの整合、`--single-file`時の日別データ
非書き出し・注記表示などを含む）。tasklist.mdのチェックボックスが更新
されていなかったため、本セッションで実態に合わせて`[x]`へ更新した。

### 品質チェック（先行実施分。タスク10でも再確認する）

- `ruff check`：`visualize.py`のimport順・未使用`import json`、
  `test_fast_client.py`の`C408`（`dict()`→リテラル）を検出、修正した。
- `ruff format`：6ファイルに整形差分があり適用した。
- `mypy`：`visualize.py`の`build_day_payload()`内、空dict初期化2箇所で
  型を推論できずエラー。明示的な型注釈（`dict[str, list[object]]`）を
  追加して解消した。
- `pytest`（`tests/trial_factory/eqp_workload_fastview`のみ）：35件成功。
- `pytest`（プロジェクト全体）：新規`eqp_workload_fastview`と旧版
  `eqp_workload_analysis`のテストファイル名が同名（`test_io.py`等）で
  かつどちらも`__init__.py`が無かったため、pytestのモジュール名衝突
  （`import file mismatch`）で全体実行が失敗した。旧版ディレクトリには
  一切手を入れない方針のため、新規側の`tests/trial_factory/
  eqp_workload_fastview/__init__.py`（空ファイル）を追加してパッケージ化
  し、旧版と異なる完全修飾モジュール名になるようにして解消した。
  修正後、`uv run pytest`は88件（旧版24件＋fastview新規35件＋共通29件）
  すべて成功。

### タスク8：性能実測

`output/proc_history_sample.parquet`（3,508,309行・設備400台、要求の
受け入れ条件と同一データ）を用い、`--input`にこのファイルを指定して
実測した。ブラウザ計測にはPlaywright(Chromium)を使用。本サンドボックス
環境にはヘッドレスChromiumの実行に必要な共有ライブラリ
（`libnspr4`/`libnss3`/`libnssutil3`/`libasound2`）が無くroot権限も
無かったため、`apt-get download`で.debを取得し`dpkg-deb -x`で
非rootに展開、`LD_LIBRARY_PATH`で読み込ませて実行した（リポジトリ・
プロジェクト依存には一切追加していない、計測用の一時セットアップ）。

- **8-1 データ生成時間**：78.06秒（`/usr/bin/time -v`実測、User
  225.18秒・308%CPU＝DuckDBの並列実行、最大RSS 2.27GB）。
  3,508,309行・設備400台・上位15台・231日分すべてに対して
  `data/days/<日付>.json`を生成。既定`--period-days`（0＝全期間）でも
  完走することを確認した。
- **8-2a 同一日付の2回目以降の切替**（キャッシュ済み、n=30）：
  中央値6.1ms／p95 13.7ms → **100ms以内の目標を達成**。
- **8-2b ロット選択（ガント区間クリック）→⑥-4更新**（n=15）：
  中央値14.0ms／p95 41.0ms → **100ms以内の目標を達成**。
- **8-3 初回の日付選択**（未キャッシュ・`fetch()`のファイルI/O含む、
  n=25）：中央値23.7ms／p95 29.8ms → **300ms以内の目標を達成**。
- **8-4 高速モード初回起動**（URLアクセス→⑥-2操作可能、n=20）：
  中央値2187ms／p95 2788ms／最大3558ms → **2秒以内の目標を未達**。

**データ件数・ファイルサイズ**（同条件、上位15台・231日分）：
`index.html`（シェル。①〜⑤・⑥-1・⑥-2のPlotly figure spec含む）
1.7MB、`data/daily_index.json`（⑥-2用の全期間日次集計）8KB、
`data/days/<日付>.json`（1日分。区間・仕掛数量・ロット明細を含む）は
231ファイルで中央値1.48MB／p95 1.62MB／最大1.65MB（データが薄い日は
最小3KB）、日別データ合計265MB（レポートディレクトリ全体268MB）。
初回の日付選択（8-3）がこの1.5MB前後のJSON取得を含んでも95パーセンタイル
30ms程度に収まっているのは、配信先がローカル`127.0.0.1`のためと考えられる。

#### 8-5：8-4未達の原因切り分け

「Plotlyライブラリを読み込むだけでチャートを1つも描画しないダミー
ページ」を作って分離計測したところ、ライブラリの読込・JS解析だけで
1.2〜2.4秒かかることを確認した。さらにリソースタイミングAPIで内訳を
見ると、CDNからのスクリプト転送は約0.5秒、DOMContentLoadedまでの
残り約2秒はブラウザがスクリプトを同期的に解析・実行する時間だった
（`<script src="...plotly...">`が`<head>`にあり`defer`/`async`が無い
ため、後続のパース・実行がブロックされる。これは`common/report.py`が
定義する共通の埋め込み方法で、旧版`eqp_workload_analysis`も同じCDN
から同じPlotlyを読み込んでいる＝fastviewが新たに持ち込んだコストでは
ない）。一方、⑥-2チャート描画完了までのfastview固有の処理
（`window.FastView`初期化・初期日ペイロードの描画）はload完了から
60〜90ms程度だった。

結論として、8-4未達の主因はfastview固有の実装ではなく、design.mdで
「既存のPlotlyを継続する」と既に決定済みの共通依存（Plotly本体の
読込・解析コスト）であり、かつ本サンドボックス環境はrequirements.md
の制約事項が明示的に対象外とする「低速ストレージ・初回ブラウザ起動・
OS負荷」の影響を強く受けている可能性が高い（同一条件の繰り返し計測でも
1.2〜3.6秒の幅があり、CPUが逼迫した検証コンテナ特有の変動と見られる）。
design.mdの決定を覆す設計変更（Plotly依存の見直し）は今回のタスクリスト
の対象外と判断し、実施しなかった。次回以降への申し送り事項に対応方針を
記録した。

### タスク9：ドキュメント更新

- `docs/trial_factory/eqp_workload_fastview.md`を`docs/templates/tool-doc.md`
  の様式で新規作成した（`docs/trial_factory/eqp_workload_analysis.md`の
  記載粒度を踏襲）。
- `docs/product-requirements.md`の受け入れ条件「可視化レポートは
  `file://`で開ける自己完結HTMLであること」・非機能要件「可搬性」に、
  `trial_factory/eqp_workload_fastview`限定の高速モード例外を追記した。
- `docs/architecture.md`の「技術的制約と要件」に「ローカル静的サーバー
  配信パターン」を新設し、`http.server.ThreadingHTTPServer`使用・
  常時稼働しない・追加依存を増やさない旨を明記した。「ブラウザ」の項にも
  例外時の前提URLを補足した。

### タスク10：品質チェック・最終確認

- `ruff check .`（全体）：**成功**（fastview新規ファイルの指摘はタスク0〜7の
  実施結果で修正済み）。
- `ruff format .`：fastview配下の新規ファイルには`--check`で差分が
  無いことを確認済み（タスク0〜7参照）。プロジェクト全体への
  `ruff format .`（`--check`無し）の実行は、`docs/reference/`配下
  （本タスクと無関係な既存ファイル）にも整形差分が入ってしまうため
  見送った。fastview配下は個別に整形適用済み。
- `mypy .`（全体）：**失敗**。ただし原因は本タスクと無関係な既存の問題
  （`src/analyse_tool/__init__.py`と`docs/reference/analyse_tool/__init__.py`
  が同じモジュール名`analyse_tool`とみなされる`Duplicate module named`
  エラー）で、`docs/reference/`は本タスクで一切変更していない
  （直近の変更コミットは`2eb3dcf docs: move completed reference
  implementation to docs/reference`で、本ブランチより前）。fastview配下
  単独では`mypy src/analyse_tool/trial_factory/eqp_workload_fastview
  scripts/trial_factory/eqp_workload_fastview.py`が成功することを
  タスク0〜7で確認済み。この既存の全体mypyエラーは本タスクのスコープ外
  のため、修正はせず申し送り事項に記録する（`docs/reference/`は永続的
  ドキュメント扱いの参考実装であり、無断で変更しない）。
- `pytest`（全体）：**88件成功**（旧版`eqp_workload_analysis`24件・
  fastview新規35件・`common`配下29件）。
- 10-4（旧版への差分確認）：`git status --short`・
  `git diff --stat -- src/analyse_tool/trial_factory/eqp_workload_analysis
  tests/trial_factory/eqp_workload_analysis
  scripts/trial_factory/eqp_workload_analysis.py
  docs/trial_factory/eqp_workload_analysis.md`のいずれも差分無しを確認した。

#### 10-5：requirements.md受け入れ条件との突き合わせ

**性能**
| 条件 | 結果 |
| --- | --- |
| サンプルデータ相当でデータ生成完了 | ✅ 78.06秒で完了（タスク8-1） |
| 初期HTMLに全期間の工程明細を埋め込まない | ✅ `index.html`はシェルのみ、明細は`data/days/`に分離 |
| 日付切替時に対象設備群×選択1日分だけ読み込む | ✅ `fetch(data/days/<日付>.json)`のみ |
| 2回目以降切替・ロット選択→⑥-4更新 100ms以内 | ✅ 中央値6〜14ms／p95 14〜41ms |
| ズーム・スクロール 100ms以内 | ✅ タスク11で追加実装。ホイールズーム中央値3.4ms／p95 9.1ms、ドラッグパン中央値2.3ms／p95 4.8ms |
| 初回日付選択 95パーセンタイル300ms以内 | ✅ p95 29.8ms |
| 高速モード初回起動 2秒以内 | ❌ 中央値2187ms／p95 2788ms（原因切り分け済み。申し送り事項） |
| 件数・ファイルサイズ・中央値・p95の記録 | ✅ タスク8実施結果に記録済み |

**表示・操作**：①〜⑤・⑥-1の開閉、⑥-2全期間日次＋日クリック連動、
⑥-3が選択日00:00〜翌日00:00、対象設備群を縦に並べ設備ごとにまとまりが
分かる表示、同一設備内重複のサブレーン分割、ガント区間内・ホバーに
`lot_id`を出さない（ホバーは装置ID・開始・終了のみ）、区間クリックで
⑥-4更新、仕掛数量推移の3分類積み上げ、⑥-4に`lot_id`列表示——いずれも
実装済みで、目視確認（デバッグスクリプトでのホバー・クリック結果）と
ユニットテストの双方で✅。

**品質**：4ステップ構成、DuckDBでの集計（pandas全件ロードなし）、
日別データ生成・サブレーン割当・画面データ読込・クリック連動への
テスト、旧版に差分無し・旧版テスト成功継続、`docs/trial_factory/
eqp_workload_fastview.md`新規作成——いずれも✅。`ruff check`／`pytest`は
全体で成功、`ruff format`はfastview配下で成功（全体`--check`無し実行は
無関係ファイルへの影響を避け見送り）、`mypy`は全体では失敗するが
原因は本タスクと無関係な既存の問題（詳細は上記）。

**総合判定（初回）**：性能の「高速モード初回起動2秒以内」が本サンド
ボックス環境では未達、「ズーム・スクロール」の性能計測は対象機能が
無いため実施不可、`mypy .`（全体）は既存の無関係な問題で失敗——の3点を
除き、受け入れ条件を満たしている。3点とも原因を特定し、対応方針
（次回以降への申し送り）を記録した。ユーザーへの最終報告時に、この
3点について続行するか・別途対応するかの判断を仰いだ。

**総合判定（ユーザー指示反映後）**：ユーザー指示（下記「最終報告後の
追加対応」参照）により、ズーム・スクロールは追加実装・実測まで完了
（✅）、`mypy .`（全体）は不要になった参考実装の削除で解消（✅）。
「高速モード初回起動2秒以内」の本サンドボックス環境での未達のみ、
ユーザー了承のうえ対応不要として確定した。以上により、requirements.md
の受け入れ条件をすべて満たす状態になった（性能の1項目のみ、本サンド
ボックス環境固有の制約としてユーザー了承済み）。

### 最終報告後の追加対応（ユーザー指示分）

上記の最終報告に対し、ユーザーから次の指示を受けた。

1. ズーム・スクロール → 今回の要件に追加して対応が必要
2. 高速モード初回起動2秒未達 → 了解（対応不要、記録のみで確定）
3. `mypy .`（全体）失敗 → `docs/reference/analyse_tool`は削除してOK。
   あわせて`customer_pref_summary`・`generate_sample_data`も削除してよい

指示3への対応として、`docs/reference/analyse_tool/`（`common/`・
`customer_pref_summary/`・`generate_sample_data/`を含む全体）と、
対応する`docs/reference/customer_pref_summary.{py,md}`・
`docs/reference/generate_sample_data.{py,md}`を削除した
（`docs/reference/generate_proc_history/`は他ツールから参照され続けて
いるため対象外、削除していない）。削除後に判明した副次的な問題も
あわせて対応した。

- `docs/reference/analyse_tool/`削除により`Duplicate module named
  "analyse_tool"`エラーは解消したが、`mypy .`を再実行すると次に
  `tests/trial_factory/eqp_workload_fastview/__init__.py`（本タスクの
  タスク0〜7でpytestのテストファイル名衝突対策として追加したもの）と
  `scripts/trial_factory/eqp_workload_fastview.py`が同じモジュール名
  "eqp_workload_fastview"とみなされる、別の`Duplicate module named`
  エラーが露見した（今まではanalyse_toolのエラーでmypyが早期終了して
  隠れていた）。
- 対応として、pytest側は`__init__.py`追加ではなく
  `pyproject.toml`の`[tool.pytest.ini_options]`に
  `addopts = "--import-mode=importlib"`を設定する方式に切り替えた
  （pytest公式が推奨する、同名テストファイル衝突の標準的な解決策。
  ファイルパスから直接importするため`__init__.py`が不要になる）。
  これに伴い`tests/trial_factory/eqp_workload_fastview/__init__.py`は
  削除した。mypy側は`[tool.mypy]`に`explicit_package_bases = true`・
  `mypy_path = "src"`を設定し、`__init__.py`の有無に頼らず
  ディレクトリ構成から一意にモジュール名を解決させた。
- 上記2つの設定後、`mypy .`を再実行すると`docs/reference/
  generate_proc_history/`（削除対象外）が`pyarrow`を直接importしている
  箇所で`import-untyped`エラーが新たに露見した（これも
  `docs/reference/analyse_tool`のエラーに隠れていた）。既存の
  `[[tool.mypy.overrides]]`（`plotly.*`/`duckdb.*`を
  `ignore_missing_imports`扱い）と同じ理由・同じパターンのため、
  対象モジュールに`pyarrow.*`を追加して解消した。
- 副産物として、削除した`docs/reference/analyse_tool/generate_sample_data/`
  配下にあった`ruff format`未整形の2ファイルも無くなり、
  `ruff format --check .`が全体で差分ゼロになった。

**再確認結果**：`ruff check .`／`ruff format --check .`／`mypy .`／
`uv run pytest`（88件）が、プロジェクト全体ですべて成功することを
確認した（`docs/reference/analyse_tool`削除前は`mypy .`のみ失敗して
いたが、今は無い）。`pyproject.toml`への変更はfastview固有の内容では
なくプロジェクト全体のテスト・型チェック設定のため、
`docs/development-guidelines.md`（テスト規約・型チェック規約）側への
反映要否は次回確認したい。

指示1（ズーム・スクロール追加）は、requirements.md／design.mdへの
追記と実装をこのあと別途進める（進捗はこのファイルの続きに追記する）。

### タスク11：⑥-3ズーム・スクロール追加

操作方式（マウスホイール＋ドラッグ）はユーザーに2択（ホイール＋ドラッグ／
ズームボタン＋スクロールバー）を提示し選択してもらった
（requirements.md「追加要件」・design.md「追加設計」参照）。

**実装**：`fast_client.py`に表示範囲状態`viewStart`/`viewEnd`
（既定`[0, 1440]`分）を追加し、`renderGantt()`の座標変換・4時間固定
だった目盛描画をこの状態基準に置き換えた。目盛は表示幅に応じて
`[5,10,15,30,60,120,240,360,720,1440]`分から本数4〜10本に収まる間隔を
選ぶ`pickTickStepMin()`で動的生成し、新設した`renderAxis()`が
`#gantt-axis`（旧: `visualize.py`側で静的生成していた`.gantt-axis`の
中身。`_build_axis_ticks_html()`は削除しJS側へ一本化）へ反映する。
ホイールでカーソル位置の時刻を中心に拡大縮小（`zoomAt()`、表示幅
30分〜1440分にクランプ）、ドラッグは`mousedown`→`mousemove`
（移動量が4pxを超えたら「パン中」に切替、ホバー・既存クリックの
ロット選択処理は抑止）→`mouseup`、ダブルクリックで全期間表示へ
リセットする。日切替（`selectDay`）のたびにも表示範囲をリセットする。
仕掛数量推移グラフ（`renderWip`）は設計判断どおり対象外とし、常に
1日分のまま変更していない。画面外（現在の表示範囲に重ならない）区間は
`renderGantt()`のループ先頭でスキップし、描画・ヒットテストの両方から
除外する（旧タスク4-2「画面外は描画しない」がズーム機能追加で初めて
意味を持つようになった）。

**ユニットテスト**：`test_fast_client.py`に5件追加（axis要素の参照、
wheel/mousedown/mouseup配線とズーム定数の存在、dblclickでのリセット
配線、`applyPayload()`内でのリセット呼び出し、パン直後のclickガード）。
既存の方針どおり、生成されたJS文字列に必要な識別子が含まれることを
検証する文字列ベースのテスト（プロジェクトの正式なpytestスイートに
追加。Playwrightは使わない）。

**Playwrightでの動作確認**（`proc_history_sample.parquet`で生成した
実レポート、対象: EQP252・lane0・1078.812〜1113.151分の区間）：
最大表示幅でのズームアウトは変化しない（クランプが効く）／ホイール
ズームインで目盛表示が変化する／ズーム後も同じカーソル位置でのホバー・
クリックが正しく効く（時刻が cursor 直下で不変に保たれる`zoomAt()`の
設計どおり）／ドラッグ後に目盛が変化しパンが効く／パン直後のクリックは
ロットを誤選択しない／ダブルクリックで初期表示の目盛に戻る／日切替で
ズーム・パン状態がリセットされる——**全項目確認OK**。

**性能実測**（同レポート、ページ内`performance.now()`で
`canvas.dispatchEvent()`呼び出し自体の所要時間を計測。ハンドラが
同期処理のため、この呼び出し時間がほぼ「操作開始から描画完了まで」に
相当する）：

- ホイールズーム1回あたり（`zoomAt`→`renderGantt`+`renderAxis`、
  n=30）：中央値3.4ms／p95 9.1ms／最大9.3ms → **100ms以内の目標を
  大きく上回って達成**。
- ドラッグパン1ステップあたり（`mousemove`→`renderGantt`+
  `renderAxis`、n=30）：中央値2.3ms／p95 4.8ms／最大5.6ms →
  **100ms以内の目標を大きく上回って達成**。

**ドキュメント更新**：`docs/trial_factory/eqp_workload_fastview.md`の
「レポートの内容」・「既知の制約・注意点」にズーム・パン操作、表示幅の
上下限（30分〜1日）、日切替でのリセット、WIPグラフが対象外であることを
追記した。

**再確認**：`ruff check .`／`ruff format --check .`／`mypy .`／
`uv run pytest`（93件、タスク11の新規5件を含む）が、プロジェクト全体で
すべて成功することを確認した。

### タスク12：⑥-3ズーム・パンと仕掛数量推移(WIP)グラフの同期

タスク11完了時点ではWIPグラフをズーム対象外（常時1日表示のアンカー）
としていたが、ユーザーから「ズーム、スクロールタイムラインと仕掛数量
グラフが同期して動作するようにして」と明示的な指示があり、方針を
撤回・変更した（requirements.md「追加要件」・design.mdの該当セクション
を2026-09-02付けで改訂、撤回の経緯も残した）。

**実装**：`renderWip()`のX軸を`wip.t_min / 1440`（1日固定）から
`(wip.t_min - viewStart) / (viewEnd - viewStart)`（ガントと同じ表示
範囲）へ変更。Y軸（`maxTotal`、縦方向のスケール）は従来どおり1日全体
（96バケット全部）の最大値で固定し、ズームしても縦の見た目は変えない
方針を維持した（1日全体に対する相対的な多さが分かるように、という
design.mdの元々の狙いはX軸同期後もY軸側で活かした）。`zoomAt()`・
ドラッグパンの`mousemove`ハンドラ・ダブルクリックリセットの3箇所すべてに
`renderWip(currentPayload)`の呼び出しを追加し、ガント（`renderGantt`+
`renderAxis`）と必ず同時に再描画されるようにした。WIPグラフにも
`ticksInView()`基準の目盛線を追加し、ガントの目盛と時間的に対応する
縦線が両グラフに表示されるようにした。

**視覚的な整列**：ガント本体は`.gantt-body-row`（`140px 1fr`グリッド）
で左側に設備ラベル列を持つが、WIPグラフ側は元々`width:100%`のみで
ラベル列分のオフセットが無く、ズーム前から実は横方向のピクセル位置が
ガントとずれていた。同期の効果が視覚的に伝わるよう、`visualize.py`に
`.wip-body-row`（同じ`140px 1fr`グリッド、左セルは空）を追加し、
WIPのcanvasをガントのcanvasと同じ横幅・同じ左端に揃えた。

**ユニットテスト**：`test_fast_client.py`に4件追加（`zoomAt`・パン用
`mousemove`ハンドラ・ダブルクリックリセットそれぞれの関数本体に
`renderWip(currentPayload)`呼び出しが含まれること、`renderWip()`の
X軸計算式が表示範囲基準に変わっていること）。既存と合わせて97件成功。

**Playwrightでの動作確認**（同じ実データレポートで生成）：
ガント・WIPのcanvas左端・幅が一致／ホイールズーム後にWIPの見た目
（`canvas.toDataURL()`のスナップショット比較）が変化する／ズーム後も
canvas位置が揃ったまま／ドラッグパン後にWIPの見た目がさらに変化する／
ダブルクリックでガント・WIPともに初期表示のスナップショットへ戻る
——**全項目確認OK**（`verify_zoom.js`によるタスク11の回帰確認も
全項目OKで、既存挙動への悪影響が無いことも合わせて確認）。

**性能再計測**（WIP再描画を含めた状態、n=30）：ホイールズーム1回
あたり中央値0.8ms／p95 5.6ms／最大7.2ms、ドラッグパン1ステップあたり
中央値0.9ms／p95 1.7ms／最大2.2ms → **いずれも100ms目標を大きく
上回って達成**（WIPは96バケット固定のため、追加コストはごく僅か）。

**ドキュメント更新**：`docs/trial_factory/eqp_workload_fastview.md`の
「レポートの内容」「既知の制約・注意点」を、WIPグラフがガントと同期する
内容に更新した（WIPは15分刻みのデータのため、最小表示幅付近では折れ線
が数点しかなく直線的に見える注意点も記載）。

**再確認**：`ruff check .`／`ruff format --check .`／`mypy .`／
`uv run pytest`（97件）が、プロジェクト全体ですべて成功することを
確認した。旧版`eqp_workload_analysis`への差分も引き続き無し。

### タスク13：⑥-3縦寸法縮小・装置ステータス背景・WIP軸目盛・待機二重計上修正

「ガントの縦を1/4に」「装置ステータスを背景で」「WIPの二重計上を検証」
という3件のユーザー指摘・指示をまとめて対応した。

- **縦寸法**：`ROW_HEIGHT_PX`/`ROW_GAP_PX`/`EQP_GAP_PX`を`22/3/8`から
  `5/1/2`へ。実測でガント高さが3320px→798px（実データ、231日中の1日）
  に縮小。設備ラベルはID表示のみに簡略化し、サブレーン数は`title`属性
  （ホバー）へ退避した。
- **装置ステータス背景**：`mergeIntervals()`で設備ごとの全サブレーン
  区間を和集合化し、Waiting全面塗り→Processing区間で上書きする2段階
  描画を`renderGantt()`の区間バー描画より前に追加した。配色は
  `#dceefb`（Processing）・`#eef0f2`（Waiting）。実データのCanvas画素を
  直接読み取り、両色が実際に描画されていることを確認した（Processing
  色が全画素の約61%を占めることを確認）。将来の`Stop`ステータス追加は
  データが無いため見送り、拡張しやすい構造だけ用意した。
- **WIP Y軸目盛**：`renderWipAxisLabels()`が0・中間・最大値を
  `#wip-axis`（ガントの設備ラベル列と同じグリッド位置）へ表示する。
- **二重計上バグ**：ユーザーの指摘どおり、対象設備群内の設備間移動で
  待機が二重計上されるバグを確認・修正した（詳細は「タスク上部の
  最終報告後の追加対応」ではなく design.md「追加設計4」参照。
  `E1→E2`両方対象の最小ケースで合計が2→1に修正されたことを確認）。

**品質チェック**：`ruff check`／`ruff format --check`／`mypy`／
`pytest`（102件）が全体で成功。Playwrightでの動作確認（縦寸法縮小・
ラベルのtitle属性・凡例表示・背景色の画素確認・ズーム後の再描画）も
全項目OK。

**ドキュメント更新の遅延について**：13-10（`docs/trial_factory/
eqp_workload_fastview.md`更新）は、着手時点でチェックのみ先に済ませて
しまい、実際の反映はタスク14と同時に行った（ユーザーからタスク14の
指示が続けて来たため）。実害は無いが、チェックを先につけて実施を後回し
にする進め方はしないほうがよい、との反省点として記録する。

### タスク14：仕掛数量推移の待機中カテゴリ統合

「待機中の区分を一つに統合してほしい」という指示を受け、待機中(自装置
着工待ち)／待機中(他装置着工待ち)の2区分を「待機中」1区分へ統合した。

- `analyze.py`：`build_day_wip_series()`の戻り列を`busy`/`wait_self`/
  `wait_other`（3列）から`busy`/`wait`（2列）に変更。二重計上修正
  （タスク13）で既に排他的になっていた2つのサブクエリを`+`で単純加算
  するだけなので、正しさへの影響は無い。
- `visualize.py`／`fast_client.py`：`wip`ペイロードを`t_min`/`busy`/
  `wait`の3キーに変更、`COLOR_WAIT_SELF`（橙）・`COLOR_WAIT_OTHER`
  （緑）は削除し、既存の`COLOR_WAIT`（グレー、旧版由来）を再利用した。
  積み上げ描画（`renderWip`）を3バンドから2バンドへ簡略化。凡例・
  タイトル文言も2分類に更新した。
- `test_analyze.py`／`test_visualize.py`／`test_fast_client.py`の
  関連テストを更新（列名・キー名・凡例数などのアサーション）。
- `requirements.md`・design.mdの該当受け入れ条件・記述を改訂（取り消し
  線を残し、いつ・なぜ変更したかを追跡できるようにした）。

**確認結果**：`ruff check`／`ruff format --check`／`mypy`／`pytest`
（102件）が全体で成功。Playwrightで実データを確認し、凡例が「着工中／
待機中」の2項目のみ、`data/days/<日付>.json`の`wip`が`t_min`/`busy`/
`wait`の3キーのみになっていること、WIP Y軸ラベル（前タスクの機能）が
引き続き表示されることを確認した。旧版`eqp_workload_analysis`への
差分も引き続き無し。
