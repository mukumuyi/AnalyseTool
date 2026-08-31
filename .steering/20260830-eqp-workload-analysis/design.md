# design.md — 設備稼働負荷・ロット待機分析ツールの設計

`requirements.md`（承認済み）に基づく実装設計。画面配置・各グラフの見せ方の
確定版は、レビューで実際に操作して確認済みのモックをそのまま確定版として
扱う（変更が無いため再公開はしない）:
https://claude.ai/code/artifact/82556c36-ee84-4dba-aa07-ed6cb68b7208

## 1. 実装アプローチ

`docs/repository-structure.md`の通常フローに従い、`.steering/`を経由して
直接`src/`+`scripts/`へ実装する（`docs/reference/`は経由しない）。これが
本リポジトリ初の「本採用」のため、`docs/repository-structure.md`・
`docs/functional-design.md`の該当記述も実装後に更新する（詳細は
「7. 影響範囲」）。

- プロジェクト名: `trial_factory`
- ツール名: `eqp_workload_analysis`
- 4ステップ構成（`prepare`/`process`/`analyze`/`visualize`）+
  `cli.py`/`io.py`
- 可視化は`docs/architecture.md`の方針通りPlotly（`fig.write_html()`、
  `include_plotlyjs="cdn"`）。前回モックのSVGはあくまで画面確認用の仮描画で
  あり、実装はPlotlyの`go.Figure`ベースに置き換える。

## 2. 変更するコンポーネント

| ファイル | 状態 | 役割 |
| --- | --- | --- |
| `src/analyse_tool/common/charts/bar.py` | 既存流用 | ②③積み上げ棒グラフ（`stacked_bar()`をそのまま利用） |
| `src/analyse_tool/common/charts/pareto.py` | 新規 | ⑥-1 パレート図（棒＋累積構成比の二軸） |
| `src/analyse_tool/common/charts/timeline.py` | 新規 | ⑥-2 装置稼働グラフ（1時間刻み積み上げ＋着工件数折れ線） |
| `src/analyse_tool/common/charts/gantt.py` | 新規 | ⑥-3 ガントチャート（並行処理枠×ロット区間）＋仕掛数量推移（3分類積み上げ面グラフ） |
| `src/analyse_tool/common/report.py` | 拡張 | 1段階（棒→明細表）から、パレート図→装置稼働グラフ→ガント+仕掛推移→明細表の4段階に一般化。既存の1段版APIは維持し後方互換を壊さない |
| `src/analyse_tool/trial_factory/eqp_workload_analysis/{cli,io,prepare,process,analyze,visualize}.py` | 新規 | 本ツール本体 |
| `scripts/trial_factory/eqp_workload_analysis.py` | 新規 | エントリポイント |
| `docs/trial_factory/eqp_workload_analysis.md` | 新規 | 説明資料 |
| `docs/functional-design.md` | 更新（実装後） | コンポーネント表の状態更新、ドリルダウン方針を4段階に拡張したことを反映 |
| `docs/repository-structure.md` | 更新（実装後） | `trial_factory`を最初の本採用プロジェクトとして記載 |
| `docs/product-requirements.md` | 更新（実装後） | 「既知のリスク」の`docs/reference/`乖離リスクの扱いを見直す |

## 3. モジュール依存関係（グラフ関連）

依頼のあった「各グラフモジュールの依存関係」をまとめる。矢印は「利用する
（import する）」方向。

```mermaid
flowchart TD
    subgraph common["src/analyse_tool/common/"]
        bar["charts/bar.py<br/>(積み上げ棒)"]
        pareto["charts/pareto.py<br/>(パレート図)"]
        timeline["charts/timeline.py<br/>(装置稼働グラフ)"]
        gantt["charts/gantt.py<br/>(ガント＋仕掛推移)"]
        report["report.py<br/>(N段ドリルダウンHTML組み立て)"]
    end
    subgraph tool["trial_factory/eqp_workload_analysis/"]
        visualize["visualize.py"]
    end

    visualize --> bar
    visualize --> pareto
    visualize --> timeline
    visualize --> gantt
    visualize --> report
    report -.->|"HTML化されたFigureを受け取るのみ<br/>（chart系モジュールをimportしない）"| pareto
    report -.-> timeline
    report -.-> gantt
```

- `common/charts/*.py`同士に依存関係は無い（それぞれ独立に
  `pandas.DataFrame`等を受け取り`go.Figure`を返すだけの純関数群）。
  `docs/architecture.md`の「共通処理は各ツールのサブパッケージに依存しない
  一方向の関係を保つ」を踏襲し、`common/`配下からツール固有コード
  （`trial_factory/*`）への依存は作らない。
- `common/report.py`は各chartモジュールが返した`go.Figure`（`.to_html()`
  可能なもの）を受け取って埋め込むだけで、`pareto.py`等を直接importして
  再生成することはしない（責務の分離。グラフの見た目を変えたい場合は
  chartモジュール側だけを直せばよい）。
- `visualize.py`が上記4モジュールを組み合わせる唯一の場所になる
  （既存`customer_pref_summary/visualize.py`と同じ位置づけ）。
- `gantt.py`は1モジュール内に「ガントチャート生成関数」と「仕掛数量推移
  生成関数」の2つを持つ（両方とも同じ時間軸データを扱うため近い場所に置く
  が、関数としては独立させ、どちらか一方だけの利用も妨げない）。

## 4. データ加工処理の依存関係（`prepare`→`process`→`analyze`→`visualize`）

依頼のあった「データ加工処理の依存関係」をまとめる。矢印は「データが
流れる」方向。

```mermaid
flowchart TD
    P["data/trial_factory/proc_history.parquet<br/>(lot_id, prodspec_id, mainpd_id,<br/>ope_no, ope_seq, eqp_id,<br/>start_time, end_time)"]

    P --> Prepare["① prepare.py<br/>profile_from_parquet()で傾向把握<br/>（件数・eqp_id種類数など）"]
    P --> Clean["② process.py: clean_proc_history()<br/>必須列の欠損・型を整形"]
    Clean --> Wait["② process.py: compute_wait_minutes()<br/>ロット内 ope_seq→ope_seq+1 の<br/>end_time/start_time差分で待機時間を算出<br/>(DuckDB window関数 LEAD)"]
    Clean --> NextEqp["② process.py: annotate_next_eqp()<br/>LEAD(eqp_id) OVER (PARTITION BY lot_id<br/>ORDER BY ope_seq) で「次工程のeqp_id」を付与<br/>LAG(eqp_id)で「前工程のeqp_id」も付与"]

    Wait --> AggBar["③ analyze.py: aggregate_eqp_workload()<br/>eqp_id別 処理数・待機時間合計/平均<br/>→①②③④⑤の元データ"]
    Wait --> AggPareto["③ analyze.py: build_pareto()<br/>待機時間合計 降順+累積構成比<br/>→⑥-1 パレート図"]
    AggPareto --> TopN["上位N台(既定15)の eqp_id リストを確定<br/>→ ⑥-2以降はこのN台分のみ深掘り対象"]

    TopN --> Hourly["③ analyze.py: build_hourly_utilization()<br/>上位N台×時間帯(1h)で<br/>着工中/待機の時間比率・着工件数を集計<br/>→ ⑥-2 装置稼働グラフ"]
    TopN --> LotDetail["③ analyze.py: build_lot_records()<br/>上位N台に関係するロットの明細<br/>(lot_id, eqp_id, ope_no, ope_seq,<br/>start_time, end_time, next_eqp_id, prev_eqp_id)<br/>→ ⑥-3 ガント/仕掛推移 と ⑥-4 明細表 の共通ソース"]
    NextEqp --> LotDetail

    LotDetail --> Gantt["④ visualize.py（ブラウザ側JS）<br/>選択eqp×時間帯のlot_recordsから<br/>並行処理枠（行）に詰め直す<br/>→ ⑥-3 ガントチャート"]
    LotDetail --> Wip["④ visualize.py（ブラウザ側JS）<br/>同じlot_recordsから<br/>着工中/待機(自装置)/待機(他装置)を集計<br/>→ ⑥-3 仕掛数量推移"]
    LotDetail --> Detail["④ visualize.py（ブラウザ側JS）<br/>クリックしたlot_idで1行に絞り込み<br/>→ ⑥-4 ロット明細表"]

    AggBar --> Report["④ visualize.py → common/report.py<br/>①〜⑥を1枚のHTMLに組み立て"]
    AggPareto --> Report
    Hourly --> Report
    LotDetail --> Report
```

ポイント:

- **①〜⑤・⑥-1（パレート図）までは`analyze.py`が集計済みの小さいDataFrame
  を作り、`visualize.py`にはそれだけを渡す**（既存方針通り）。
- **⑥-2（装置稼働グラフ）は上位N台分だけを`analyze.py`で事前集計**する
  （全400台分は作らない）。
- **⑥-3（ガント＋仕掛推移）と⑥-4（明細表）は、`analyze.py`が作る
  「上位N台に関係するロット明細（`LotDetail`）」という1つの共通データを
  ソースにする**。装置稼働グラフの1時間棒をクリックした時点で新たに
  Pythonを呼び直すことはできない（`file://`で開く自己完結HTMLのため）ので、
  クリック時の絞り込み・再集計（並行枠への詰め直し・3分類の件数集計）は
  ブラウザ側のJSで行う。ここは`common/report.py`が既に採用している
  「明細データをJSONで埋め込み、クリック時にJSで絞り込む」方式の延長線上
  にある。
- **`process.py`の`annotate_next_eqp()`**（`LEAD(eqp_id)`）が仕掛数量推移の
  3分類判定の起点になる。定義は次の通り（design確定事項）:
  - **待機中（自装置着工）**: 待機中のロットのうち、次工程の`eqp_id`が
    選択中の装置と一致するもの（＝これからこの装置に来る＝この装置の
    入り待ち行列）
  - **待機中（他装置着工）**: 待機中のロットのうち、直前工程の`eqp_id`が
    選択中の装置と一致し、かつ次工程の`eqp_id`が選択中の装置と異なるもの
    （＝この装置を出た直後で、別の装置に向けて待っている＝出口側の滞留）
  - この2分類だけでは「この装置に無関係な、工場内の他の待機ロット」は
    どちらにも属さず含まれない（意図的。この装置の稼働と直接関係する
    範囲に絞ることで、母数が工場全体のロット数に膨れ上がるのを防ぐ）。

## 5. データ量対策（`LotDetail`のサイズ管理）

`requirements.md`の受け入れ条件「全設備・全期間の初期表示で密集させない」
「大量データをそのまま埋め込まない」に対応する具体策:

- `LotDetail`は**パレート図で確定した上位N台（既定15台）のみ**を対象にする
  （全400台分は作らない）。
- 上位15台×平均処理数（既存サンプルで約10,500件/台）だと、そのままでは
  15万行規模になり埋め込みには重い。そのため`analyze.py`側でさらに
  **`time_range`のうち代表的な1区間（既定: 最初の3日間、`--gantt-days`等で
  可変にする）に絞った`LotDetail`のみ**をHTMLに埋め込む。装置稼働グラフの
  1時間棒（24時間分）は、この絞り込んだ区間内の時間帯のみクリック可能に
  し、その旨をUI上に注記する（「直近3日間のみドリルダウン可」等）。
- 上記の絞り込み日数・件数上限は実データ（`prepare.py`のプロファイル結果）
  を見て`tasklist.md`実装時に具体値を確定する。埋め込みJSONが大きくなり
  すぎる場合は、`common/report.py`の`max_detail_rows`と同様に上限件数を
  設け、超過時はその旨を注記する。

## 6. `common/report.py`の拡張方式

現状の`build_bar_click_detail_html()`（1段: 棒グラフ→明細表）は変更せず
残す（`customer_pref_summary`が利用中のため）。新たに、`docs/functional-design.md`
の「ドリルダウンの二段拡張」で構想されていたフィルタ条件リスト方式を
実装した関数を追加する。

- 新関数（案）: `build_multi_stage_drilldown_html()`
  - 引数: 各段のFigure（`figs: list[go.Figure]`）、最終段の明細
    DataFrame、段間の対応付け設定（各段のクリックで何が決まるか）。
  - 今回のツール固有の事情（⑥-3が「グラフ2枚（ガント＋仕掛推移）が
    同時に1段として現れる」）に対応するため、1段に複数Figureを許容する
    （`stage_figs: list[list[go.Figure]]`のようなイメージ）。
  - 段2→段3、段3→段4の絞り込みロジック（時間帯選択、ロット選択）は
    ツール固有の解釈が要るため、絞り込み用のJSスニペット自体は
    `visualize.py`側でパラメータ化して`report.py`に渡す
    （`report.py`は組み立てに徹し、ドメイン知識を持たない既存方針を踏襲）。
  - 詳細な関数シグネチャ・JSのAPI設計は`tasklist.md`着手時に確定する
    （既存`build_bar_click_detail_html()`のテンプレート機構を土台にする）。

## 7. 各グラフの見せ方（確定版）

Artifactモック（上記URL）の通りとし、以下はPlotly実装時のパラメータ確定
事項。

| グラフ | 種類 | 軸 | 初期表示 | 備考 |
| --- | --- | --- | --- | --- |
| ①設備ごとの処理数 | 棒 | x=eqp_id, y=処理数 | 処理数降順・上位15台 | `common/charts/bar.py`は色分け前提のため、単色棒はpareto.py内の単純棒で代用するか、bar.pyに`color`省略時の単色モードを追加するかをtasklist時に決定 |
| ②③待機時間合計/平均 | 棒 | x=eqp_id, y=分 | 上位10台 | 同上 |
| ④⑤散布図 | scattergl | x=処理数, y=待機時間 | 全上位15台点表示 | `common/charts/scatter.py`は未実装のため新規実装が必要（`docs/functional-design.md`に追記） |
| ⑥-1パレート図 | 棒＋線（2軸） | x=eqp_id（待機時間合計降順）, y1=待機時間合計, y2=累積構成比(0-100%) | 上位15台、累積80%ラインの目安線を表示 | クリックでeqp_id選択 |
| ⑥-2装置稼働グラフ | 積み上げ棒＋線（2軸） | x=時刻(1h), y1=着工中/待機の時間比率, y2=着工件数 | 選択eqpの24時間 | クリックで時間帯選択（5.のデータ量対策により選択可能な範囲を絞る場合あり） |
| ⑥-3ガントチャート | 水平棒（`base`+`x`で区間表現） | y=並行処理枠（行）, x=時刻 | 選択eqp・選択時間帯を中心とした窓（既定4時間） | 着工中区間に`lot_id`をテキスト表示、待機はグレー |
| ⑥-3仕掛数量推移 | 積み上げ面（`stackgroup`） | x=時刻（ガントと共通）, y=ロット数 | ガントと同じ窓 | 3分類（着工中／待機中(自)／待機中(他)） |
| ⑥-4ロット明細表 | HTML表 | - | 選択ロット1件（同一lot_id内の全工程行も参考として表示するかはtasklist時に決定） | `common/report.py`の明細表描画を流用 |

`common/charts/scatter.py`が未実装だった点は、要件定義時に見落としていた
ため、ここで`docs/functional-design.md`のコンポーネント表に合わせて
新規実装対象に加える（④⑤で使用）。

## 8. 影響範囲の分析（実装後に反映する永続的ドキュメント）

- `docs/functional-design.md`
  - コンポーネント表: `pareto.py`/`timeline.py`/`gantt.py`/`scatter.py`を
    「実装済み」に更新
  - 「ドリルダウンの二段拡張」節: 実際に4段階（うち1段2Figure構成）まで
    一般化したことを追記し、`build_multi_stage_drilldown_html()`の設計を
    反映
  - 「ツールごとの実装」表に`eqp_workload_analysis`を追加
- `docs/repository-structure.md`
  - 「現時点では具体的なプロジェクトが1つも本採用されていない」という
    記述を、`trial_factory`が最初の本採用プロジェクトであることが分かる
    ように更新
- `docs/product-requirements.md`
  - 「既知のリスク」の`docs/reference/`乖離リスクは、
    `customer_pref_summary`・`generate_sample_data`がまだ`docs/reference/`
    に残っている間は解消しない（今回の対象外）ため、リスク文言はそのまま
    残す旨を明記するに留める（削除しない）

## 9. 実装時に確定する残課題（tasklist.md着手前に軽く合意を取る）

- ⑥-3の窓幅（既定4時間、モック準拠）・ドリルダウン対象期間（既定3日間）の
  既定値は、実データ（`prepare.py`の結果）を見てから微調整してよいか
- `common/charts/bar.py`に単色モードを足すか、pareto.py内で単純な棒を
  自前実装するか
- ロット明細表は1ロット1行のみか、そのロットの全工程行を並べるか
