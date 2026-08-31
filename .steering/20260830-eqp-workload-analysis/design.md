# design.md — 設備稼働負荷・ロット待機分析ツールの設計

`requirements.md`（承認済み）に基づく実装設計。`docs/templates/design.md`
の構成に従う。

## 対象

`trial_factory`プロジェクトの`eqp_workload_analysis`ツールを、本リポジトリ
初の「本採用」として`src/`+`scripts/`に新規実装する
（`docs/repository-structure.md`の通常フロー通り、`docs/reference/`は
経由しない）。4ステップ構成（`prepare`/`process`/`analyze`/`visualize`
+`cli.py`/`io.py`）、可視化はPlotly（`fig.write_html()`、
`include_plotlyjs="cdn"`）。

### 構成物一覧

| 種別 | 名称 | 対応種別 | 内容 |
| --- | --- | --- | --- |
| 画面 | 設備稼働負荷・ロット待機分析レポート | 新 | proc_historyを対象に①〜⑥の6セクションを1枚のHTMLにまとめる（画面レイアウト参照） |
| グラフ | パレート図（⑥-1） | 新 | 設備別の待機時間合計を降順＋累積構成比で表示 |
| グラフ | 装置稼働グラフ（⑥-2） | 新 | 選択設備の1時間刻み稼働状況＋着工件数 |
| グラフ | ガントチャート（⑥-3上段） | 新 | 選択設備・時間帯のロット単位区間（並行処理枠に対応） |
| グラフ | 仕掛数量推移（⑥-3下段） | 新 | 着工中／待機中(自装置)／待機中(他装置)の3分類積み上げ面 |
| コード | `common/charts/{bar,barline,area,gantt,scatter}.py` | 新 | 第1層（見た目の型）。`bar.py`のみ既存に単色モードを追加 |
| コード | `common/charts/{pareto,twograph}.py` | 新 | 第2層（分析の型）。描画は第1層に委譲する |
| コード | `common/report.py` | 変 | 1段階（棒→明細表）から、4段階の逐次クリック型ドリルダウンに拡張。既存の1段版APIは維持 |
| コード | `trial_factory/eqp_workload_analysis/{cli,io,prepare,process,analyze,visualize}.py` | 新 | ツール本体 |
| コード | `scripts/trial_factory/eqp_workload_analysis.py` | 新 | エントリポイント（`customer_pref_summary`と同じ、`main()`を呼ぶだけの薄いラッパー） |
| データ | `EqpWorkloadDF`／`ParetoDF`／`HourlyDF`／`LotDetail` | 新 | `analyze.py`が作る集計データ（機能別処理フロー参照） |
| データ | `wait_minutes`／`next_eqp_id`／`prev_eqp_id` | 新 | `process.py`が`proc_history`に付与する列 |
| ドキュメント | `docs/trial_factory/eqp_workload_analysis.md` | 新 | 説明資料 |
| ドキュメント | `docs/functional-design.md` | 変 | 層構造の原則・コンポーネント表・ドリルダウン方針を反映（先行反映済み） |
| ドキュメント | `docs/development-guidelines.md` | 変 | `visualize.py`肥大化対策を反映（先行反映済み） |
| ドキュメント | `docs/repository-structure.md` | 変 | `trial_factory`を最初の本採用プロジェクトとして記載（実装後） |
| ドキュメント | `docs/product-requirements.md` | 変 | 「既知のリスク」の`docs/reference/`乖離リスクの扱いを見直す（実装後） |

## 画面レイアウト

確定版はレビューで実際に操作して確認済みのモックをそのまま用いる
（変更が無いため再公開はしない）:
https://claude.ai/code/artifact/82556c36-ee84-4dba-aa07-ed6cb68b7208

各グラフの種類・軸・初期表示・備考:

| グラフ | 部品（層） | 種類 | 軸 | 初期表示 | 備考 |
| --- | --- | --- | --- | --- | --- |
| ①設備ごとの処理数 | `bar.py`(第1層) | 単色棒 | x=eqp_id, y=処理数 | 処理数降順・上位15台 | |
| ②③待機時間合計/平均 | `bar.py`(第1層) | 単色棒 | x=eqp_id, y=分 | 上位10台 | |
| ④⑤散布図 | `scatter.py`(第1層) | scattergl | x=処理数, y=待機時間 | 上位15台点表示 | |
| ⑥-1パレート図 | `pareto.py`→`barline.py` | 棒＋線（2軸） | x=eqp_id（待機時間合計降順）, y1=待機時間合計, y2=累積構成比 | 上位15台、累積80%目安線 | クリックでeqp_id選択 |
| ⑥-2装置稼働グラフ | `barline.py`(第1層) | 積み上げ棒＋線（2軸） | x=時刻(1h), y1=着工中/待機比率, y2=着工件数 | 選択eqpの代表期間分（既定3日間＝72本） | クリックで時間帯選択 |
| ⑥-3ガント | `twograph.py`→`gantt.py` | 水平棒（`base`+`x`） | y=並行処理枠（行）, x=時刻 | 選択時間帯を中心とした窓（既定4時間） | 着工中区間に`lot_id`表示、待機はグレー。並行数についての注記あり（課題対応参照） |
| ⑥-3仕掛数量推移 | `twograph.py`→`area.py` | 積み上げ面（階段状） | x=時刻（ガントと共有） | ガントと同じ窓 | 3分類。`shared_xaxes=True`でガントとズーム・パン連動 |
| ⑥-4ロット明細表 | `common/report.py` | HTML表 | - | 選択ロット1件 | |

## 画面遷移図

```mermaid
flowchart LR
    S0["①〜⑤<br/>棒グラフ・散布図（常時表示）"]
    S1["⑥-1<br/>パレート図"]
    S2["⑥-2<br/>装置稼働グラフ（選択装置）"]
    S3["⑥-3<br/>ガント＋仕掛数量推移（選択装置・時間帯）"]
    S4["⑥-4<br/>ロット明細表（選択ロット）"]

    S1 -->|"棒をクリック→装置を選択"| S2
    S2 -->|"1時間分の棒をクリック→時間帯を選択"| S3
    S3 -->|"着工中区間をクリック→ロットを選択"| S4
```

## 機能別処理フロー

表記方法は`docs/diagram-guidelines.md`の「アクティビティ図（処理順序図）の
描き方」に従う（モジュール間の呼び出し関係＝importの方向は次節
「コンポーネント構成図」を参照。混ぜない）。

### `prepare.py`（EDA・DuckDB SQL、独立した枝）

`profile_from_parquet()`の結果は`write_profile()`で`profiles/`配下に
JSONとして書き出すだけで、レポート組み立てには使わない
（既存`customer_pref_summary`と同じ位置づけ）。

```mermaid
flowchart TD
    subgraph SW1["prepare.py"]
        Start1((開始)) -->
        RawData1[("proc_history.parquet")] -->
        Check1("傾向を把握する<br/>（件数・eqp_id種類数などをSQLで集計）") -->
        ProfileData1[("ProfileData<br/>（JSON、profiles/へ書き出し）")] -->
        End1((終了))
    end
```

### `process.py`（クレンジング・DuckDB SQL）

```mermaid
flowchart TD
    subgraph SW2["process.py"]
        Start2((開始)) -->
        RawData2[("proc_history.parquet")] -->
        Clean2("clean_proc_history()<br/>必須列の欠損・型を整形") -->
        Annotate2("annotate_lot_sequence()<br/>lot_idごとにope_seq順に並べ、1回のSELECT文で<br/>wait_minutes = start_time − LAG(end_time)<br/>next_eqp_id = LEAD(eqp_id)<br/>prev_eqp_id = LAG(eqp_id) を付与") -->
        AnnotatedData2[("付与後のproc_history<br/>（DuckDBリレーション、〜数百万行）")] -->
        End2((終了))
    end
```

待機時間の算出と次工程/前工程の付与は同じSELECT文にまとめ、数百万行の
テーブルを2回スキャンしない。

### `analyze.py`（集計・DuckDB SQL→pandas）

```mermaid
flowchart TD
    subgraph SW3["analyze.py"]
        Start3((開始)) --> In3[("process.pyの出力")]
        In3 --> AggBar3("aggregate_eqp_workload()<br/>eqp_idごとにCOUNT(*)・SUM(wait_minutes)・<br/>AVG(wait_minutes)を集計（SQL→ここで.df()、約400行）")
        AggBar3 --> WorkloadDF3[("EqpWorkloadDF<br/>①〜⑤の元データ")]
        WorkloadDF3 --> Pareto3("build_pareto()<br/>待機時間合計の降順に並べ替え、<br/>累積構成比列を追加（pandas、約400行なので軽い）")
        Pareto3 --> ParetoDF3[("ParetoDF<br/>⑥-1の元データ")]
        ParetoDF3 --> Decide3{"上位N台(既定15)・<br/>代表期間(既定3日間)を決定"}
        Decide3 --> Hourly3("build_hourly_utilization()<br/>1時間ごとの着工比率・着工件数を、<br/>generate_series+区間交差のSQLで集計<br/>（Pythonでロットごとに按分しない）")
        In3 --> Hourly3
        Hourly3 --> HourlyDF3[("HourlyDF<br/>⑥-2の元データ")]
        Decide3 --> LotDetail3("build_lot_records()<br/>上位N台×代表期間のロット明細をSQLで抽出")
        In3 --> LotDetail3
        LotDetail3 --> LotDetailData3[("LotDetail（数千行）<br/>⑥-3・⑥-4の元データ")]
        WorkloadDF3 --> End3((終了))
        HourlyDF3 --> End3
        LotDetailData3 --> End3
    end
```

数百万行を扱うのは`process.py`まで。`analyze.py`に入った時点で
`EqpWorkloadDF`（約400行）・`HourlyDF`（数百行）・`LotDetail`（数千行）の
いずれかまで小さくなっており、それ以降だけがpandas・ブラウザJSに渡る。

### `visualize.py` + `common/report.py`

```mermaid
flowchart TD
    subgraph SW4["visualize.py + common/report.py"]
        Start4((開始)) --> In4[("analyze.pyの出力<br/>（EqpWorkloadDF・ParetoDF・HourlyDF・LotDetail）")]
        In4 --> Build4("コンポーネント構成図のchartモジュールを呼び、<br/>①〜⑥-2の各go.Figureを作る")
        Build4 --> Figs4[("①〜⑥-2のgo.Figure群")]
        Figs4 --> Assemble4("report.pyへFigure群とLotDetailを渡し、<br/>1枚の自己完結HTMLに組み立てる")
        In4 --> Assemble4
        Assemble4 --> Html4[("レポートHTML<br/>（LotDetailはcolumnar JSONとして埋め込み）")]
        Html4 --> End4((終了))
    end
```

ここで`uv run python scripts/...`のPythonプロセスは終了する。

### ブラウザ（HTMLを開いた後・クリックのたびに動くJS）

```mermaid
flowchart TD
    subgraph SW5["ブラウザ"]
        Start5(("HTMLを開く<br/>（都度・何度でも）")) --> Html5[("埋め込み済みLotDetail")]
        Html5 --> Gantt5("並行処理枠（行）に詰め直す<br/>→⑥-3上段(gantt)")
        Html5 --> Wip5("3分類を集計<br/>→⑥-3下段(area)")
        Html5 --> Detail5("クリックしたlot_idで1行に絞り込む<br/>→⑥-4明細表")
        Gantt5 --> End5((終了))
        Wip5 --> End5
        Detail5 --> End5
    end
```

Pythonプロセス終了後の別処理であり、スクリプト実行1回に対して0回〜
何度でも起こりうる（`process.py`〜`visualize.py`の一本道とは性質が違う）。

## コンポーネント構成図

グラフ部品は「見た目の型（第1層）」と「分析の型（第2層）」の層構造を採る。
矢印は「利用する（import する）」方向。

```mermaid
flowchart TD
    subgraph L3["案件固有: trial_factory/eqp_workload_analysis/"]
        vis["visualize.py<br/>レポート全体の調整・グラフ配置・<br/>部品へのパラメータ受け渡し"]
    end

    subgraph L2["第2層＝分析の型: common/charts/"]
        pareto["pareto.py<br/>(降順ソート・累積構成比・80%線)"]
        twograph["twograph.py<br/>(x軸共有の2段組、shared_xaxes=True)"]
    end

    subgraph L1["第1層＝見た目の型: common/charts/"]
        barline["barline.py<br/>(棒 + 第2軸の折れ線)"]
        bar["bar.py<br/>(積み上げ棒・既存＋単色モード追加)"]
        area["area.py<br/>(積み上げ面・階段状可)"]
        gantt["gantt.py<br/>(区間の水平棒、1本のgo.Barにまとめる)"]
        scatter["scatter.py<br/>(散布図・scattergl固定)"]
    end

    subgraph SH["ドリルダウン機構: common/"]
        report["report.py<br/>(4段クリック連動の組み立て)"]
    end

    vis -->|"⑥-1 パレート図"| pareto
    vis -->|"⑥-2 装置稼働グラフ"| barline
    vis -->|"⑥-3 ガント＋仕掛推移"| twograph
    vis -->|"①〜③ 棒"| bar
    vis -->|"④⑤ 散布図"| scatter
    vis -->|"段構成の設定を渡す"| report

    pareto --> barline
    twograph --> gantt
    twograph --> area
```

層をまたぐ一方向依存のみ許可し、同一層内の依存は禁止する。`common/report.py`
はどのchartモジュールもimportせず、`visualize.py`が組み立てた`go.Figure`
（各段1つ。`twograph.py`のsubplot構成も「1段1Figure」として扱える）を
受け取って埋め込むだけの機構に徹する。`common/`配下からツール固有コード
（`trial_factory/*`）への依存は作らない。

## 課題対応

| 課題 | 対応 |
| --- | --- |
| ガントチャートの並行処理枠は何行を想定するか | モックの3〜4行は実データ（`data/trial_factory/proc_history.parquet`をDuckDBのスイープライン集計で実測）に対して不足していた（設備あたり同時並行ピークは平均9・最大16）。行数は貪欲法（区間スケジューリング、O(n log n)）の詰め直し結果に応じて可変にし、縦スクロール前提にする。これは`generate_proc_history`が設備の同時使用制約（1台1ロット）を実装していない副作用であり、実際の工場のバッチ挙動ではないため、画面に「サンプルデータは設備の同時使用制約を持たないため並行数が多く出る」旨を注記する |
| `common/report.py`のドリルダウンのデータ契約 | 段によって鍵の候補数が大きく違う（eqp_idは15種類だが、eqp×時間帯は15×72=1080通り）。段1→段2（パレート図→装置稼働グラフ）は**選択式**（Pythonが上位15台分の`go.Figure`を全て事前レンダリングし、クリックは表示/非表示の切り替えのみ）、段2→段3・段3→段4は**構築式**（候補数が多すぎるため、絞り込み済み`LotDetail`から都度JSが図・表を組み立てる）に分ける。`report.py`自体はdiv配置と埋め込みJSONの書き出しのみを持ち、ドメイン固有のJSは`visualize.py`側から渡す |
| `twograph.py`（ガント＋仕掛推移）内でのクリック分離 | 1つのFigure内の2段に対する`plotly_click`はどちらの段のクリックでも発火する。ガントのtraceを1本の`go.Bar`にまとめたうえで、`twograph.py`がガントのtraceを`curveNumber === 0`に固定する順でtraceを追加することで、ガント側だけを確定的に判定できる。実機での動作確認は残課題とする |
| 仕掛数量推移の3分類の定義 | 待機中（自装置着工）＝次工程の`eqp_id`が選択中の装置と一致（これから来る）。待機中（他装置着工）＝直前工程の`eqp_id`が選択中の装置と一致し、かつ次工程が別の装置（出た直後）。この2分類に属さない工場内の他の待機ロットは対象に含めない（母数が膨れ上がるのを防ぐ意図的な絞り込み） |
| `visualize.py`が案件の増加に伴い肥大化しないか | 集計・描画ロジックは持たせず「どのグラフをどの段に置くか」の決定だけにする。セクションごとに小さいプライベート関数へ分割し、`common/`への切り出しは「2ツール以上で同じ組み立てパターンが必要になってから」に限る（1ツールの段階で先回りしない） |
| ロットの着工区間（ガントの四角）の描画・データ量 | 区間ごとに`add_trace()`せず、`x`/`base`/`y`/`marker_color`/`text`を配列にして1本の`go.Bar`にまとめる。ロットIDのラベルは区間の幅で出し分ける。埋め込みJSONは records 形式でなく columnar 形式にしてサイズを削減する |

## 残課題

- `bar.py`の単色モード追加のシグネチャ（`stacked_bar()`の引数をオプショナル
  化するか、別関数`simple_bar()`を足すか）
- `annotate_lot_sequence()`の境界ケース: ロットの最初の工程は
  `prev_eqp_id`が`NULL`、最後の工程は`next_eqp_id`が`NULL`になる。仕掛
  数量推移の3分類判定はこの`NULL`をどちらにも該当しないとして扱う
  （ユニットテストの項目に明記する）
- 仕掛数量推移の3分類が実データでどの程度意味のある分布になるかは
  `prepare.py`実装後に確認する
- ⑥-3の窓幅（既定4時間）・代表期間（既定3日間）は、実データを見て微調整
  してよい
- ロット明細表は1ロット1行のみか、そのロットの全工程行を並べるか
- `twograph.py`のクリック分離（`curveNumber`判定）は、実装の初期タスクと
  して小さいサンプルで動作確認する
