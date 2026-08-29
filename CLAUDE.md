# AnalyseTool プロジェクトルール

DATA分析で使うツールスクリプトを溜めていくプロジェクト。個々のスクリプトは
独立して実行できるツールとして `scripts/` に置く。

## 最重要ルール1: モジュール分割をしっかり行う（前準備→データ加工→分析→可視化）

`scripts/<name>.py` に処理を全部書かず、責務ごとにモジュールを分ける。
1ファイルに読み込み・加工・集計・出力・CLIが全部乗った「大きい1本のスクリプト」
にしないこと。

- `scripts/<name>.py` は**エントリポイントに徹する**。`src/analyse_tool/<name>/`
  の `main()` を呼び出すだけの薄い層にする。
- 実処理は `src/analyse_tool/<name>/` にツールごとのサブパッケージとして置き、
  機能を次の**4ステップ**で分割する。ステップは互いの実装を意識せず、
  「データを受け取り、加工済みのデータを返す」形の関数として繋げる。
  この4ステップは、一般的なデータ分析プロセス（EDA → データクレンジング/
  前処理 → 分析・モデリング → 可視化・レポーティング）に対応させている。
  1. **前準備 (`prepare.py`)** = **EDA（探索的データ分析）** — 読み込んだ
     生データの**傾向を把握する**プロファイリング処理（件数・欠損率・型・
     分布・値のばらつき・カテゴリ列のユニーク値など）。ここで得た傾向を
     もとに、後続のデータ加工・分析の方針を決める。「データの中身を知る」
     ステップであり、加工そのもの（結合・集計・変換）は行わない。
     数百万〜数億行規模を想定し、集計は極力 DuckDB の SQL で行い、
     全件を pandas にロードしない（詳細は後述「大規模データの扱い」）。
     得られた傾向は `src/analyse_tool/common/profile.py` の
     `DatasetProfile` 形式でJSON保存する（`profile_from_parquet()` で
     生成できる）。この形式は `generate_sample_data`
     ツール（後述）の入力フォーマットと共通になっている。
  2. **データ加工 (`process.py`)** = **データクレンジング/前処理
     （Data Cleaning / Preprocessing）** — 型変換・欠損値処理・結合・
     集約・特徴量作成など、分析対象のデータそのものを作る変換処理。
     数百万〜数億行規模を想定し、**Parquet + DuckDB** を標準の加工手段と
     する（詳細は後述「大規模データの扱い」）。
  3. **分析 (`analyze.py`)** = **分析・モデリング（Analysis / Modeling）**
     — 加工済みデータに対する集計・統計量算出・比較など、数値としての
     分析結果を作る処理。可視化に渡すのは生データではなく、ここで
     集計・要約した後の小さいデータにする（可視化ステップの負荷を下げる
     ため。詳細は後述）。
  4. **可視化 (`visualize.py`)** = **可視化・レポーティング
     （Visualization / Reporting）** — 分析結果をグラフ・表など見せる形に
     変換・出力する処理。可視化した内容を探索的に分析することが多いため、
     静的な画像だけでなく**インタラクティブなレポート**（ズーム・ホバー・
     フィルタ等が効くもの）も作れるようにする。標準では
     [Plotly](https://plotly.com/python/) を使い、サーバー起動が不要な
     自己完結HTML（`fig.write_html()`）として `output/` に書き出す形を
     基本とする。静的画像（PNG等）はdocsへの貼り付けや軽量な確認用として
     必要に応じて併用する。グラフの種類ごとのモジュール化・大量データ時の
     軽量化方針は後述「可視化のモジュール化と大量データ対策」を参照。
- 上記4ステップに加えて、`cli.py`（引数定義）・`io.py`（ファイルそのものの
  読み書き）を分離する。4ステップの関数はファイルI/Oを直接行わず、
  `io.py` 経由でデータの受け渡しをする。
- 4ステップを順番に呼び出す `main()` は `__init__.py`（または
  `pipeline.py`）に置く。
- 複数ツールで共通する処理（共通I/Oヘルパー等）は `src/analyse_tool/common/`
  に切り出し、各ツールのサブパッケージから読み込む。
- 1モジュール・1関数がやることは1つに絞る。長くなってきたら早めに分割する。

### 例: `sales_summary` というツールを作る場合

```text
scripts/
└── sales_summary.py           # エントリポイント（cli呼び出し＋main()呼び出しのみ）

src/analyse_tool/
├── common/
│   └── charts/                 # グラフ種類ごとの共通モジュール（全ツール共用）
│       ├── line.py
│       └── bar.py
└── sales_summary/
    ├── __init__.py             # 4ステップを順に呼ぶ main()
    ├── cli.py                  # 引数定義
    ├── io.py                   # 入出力（DuckDBでParquetを読み書き）
    ├── prepare.py              # ① 前準備（DuckDBでデータ傾向を把握）
    ├── process.py              # ② データ加工（DuckDBのSQLで集計・結合）
    ├── analyze.py              # ③ 分析（可視化用に集計・サンプリング）
    └── visualize.py            # ④ 可視化（common/charts/ を組み合わせてレポート化）

docs/
└── sales_summary.md            # 説明資料（処理概要・I/O・実行オプション）
```

### 例外: 4ステップに当てはまらないユーティリティスクリプト

`generate_sample_data`（サンプルデータ生成）のように、実データを
分析するのではなく**データそのものを作る／変換する**ようなツールは
前準備/データ加工/分析/可視化の4ステップに強引に当てはめない。
その場合も以下は変わらず適用する。

- `scripts/<name>.py` はエントリポイントに徹する。
- 実処理は `src/analyse_tool/<name>/` に置き、責務ごとに
  モジュールを分ける（例: `cli.py` / `io.py` / 処理本体のモジュール）。
- 最重要ルール2（説明資料を残す）は変わらず必須。

```text
scripts/
└── generate_sample_data.py    # エントリポイント

src/analyse_tool/generate_sample_data/
├── __init__.py                 # main()
├── cli.py                      # 引数定義
├── io.py                       # プロファイル読み込み・Parquet書き出し
└── generate.py                 # データ生成ロジック本体

profiles/
├── customers.json              # データ定義情報（プロファイル）の例
└── orders.json

docs/
└── generate_sample_data.md
```

## 用意されているユーティリティツール

### `generate_sample_data` — サンプルデータ生成

データ定義情報（プロファイルJSON）を読み込み、それに従ったサンプルデータを
Parquetで生成するツール。分析ツールを新しく作るとき、実データがまだ
手元に無い／実データを直接使えない場合は、このツールでテストデータを
用意してから `prepare`〜`visualize` の実装を進める。

```bash
uv run python scripts/generate_sample_data.py \
  --profile profiles/orders.json \
  --output output/orders_sample.parquet \
  --rows 10000000   # 省略時はプロファイルの row_count
```

- `profiles/customers.json` / `profiles/orders.json` に、汎用の業務データ
  （顧客・注文）の定義例が用意されている。列を増やす・出現割合を変えるなど
  自由に編集してよい。
- プロファイルは手書きのほか、実データがあれば
  `src/analyse_tool/common/profile.py` の `profile_from_parquet()` で
  自動生成できる（`prepare.py` が使う想定の関数）。
- `--rows` で行数を指定行数に上書きできるので、大規模データでの動作確認
  （数百万〜数億行）にもそのまま使える。
- 詳細は [docs/generate_sample_data.md](docs/generate_sample_data.md) を参照。

## 大規模データの扱い（Parquet + DuckDB）

`prepare.py` / `process.py` は数百万〜数億行のデータを扱うことを基本前提に
設計する。

- データ形式は **Parquet** を標準とする（`data/` に置く入力データ、
  `process.py` が生成する中間ファイル、いずれも）。
- 加工・集計は **DuckDB**（SQL）を第一選択にする。`io.py` で
  `duckdb.sql("SELECT ... FROM read_parquet('...')")` のようにSQLで
  フィルタ・結合・集計まで済ませ、**pandas には集計済み・絞り込み済みの
  小さいデータだけを渡す**。生データ全件を先に pandas の DataFrame へ
  読み込んでから加工しない。
- `prepare.py` のプロファイリング（件数・欠損率・分布など）も同様に、
  `COUNT` / `AVG` / `APPROX_COUNT_DISTINCT` などDuckDBのSQL集計を優先し、
  全件を pandas にロードしない。
- 依存: `duckdb`, `pyarrow`（初回使用時に `uv add duckdb pyarrow`）。
- この方針は `bussiness/ER_DuckDB` での実測（同一処理でDuckDBが
  pandas+CSV比で数百〜千倍高速）を踏まえたもの。

## 可視化のモジュール化と大量データ対策

- グラフは**種類ごとに** `src/analyse_tool/common/charts/` にモジュール化
  する（例: `line.py` / `bar.py` / `scatter.py` / `heatmap.py`）。各モジュール
  は「データを受け取り Plotly の `Figure` を返す」関数を持ち、ツールをまたいで
  使い回す。個別のグラフ描画ロジックをツールごとに再実装しない。
- 各ツールの `visualize.py` は `common/charts/` の関数を呼び出し、複数グラフを
  1つのレポート（HTML）に組み立てる役割に徹する。
- インタラクティブレポートは大量データで重くなりやすいため、次を基本方針とする。
  1. **可視化には集計済みの小さいデータだけを渡す** — `analyze.py` 側で
     表示に必要な粒度まで集計・サンプリングしてから `visualize.py` に渡す。
     生データ（数百万〜数億行）をそのままグラフライブラリに渡さない。
  2. **大量点が必要な場合はWebGLレンダラを使う** — Plotly の `scatter` ではなく
     `scattergl`（WebGL）を使う。`common/charts/scatter.py` 側で既定にする。
  3. **描画点数に上限を設ける** — 目安として数万点程度（要調整）を超える場合は
     等間隔サンプリングやビニング集計で自動的に間引く。
  4. **HTMLファイルサイズを抑える** — 複数グラフを1つのHTMLにまとめる際は
     `include_plotlyjs="cdn"` を使い、plotly.js本体を毎回埋め込まない。

### 採用技術の判断: WebGL（Plotly `scattergl`）を既定にする

大量データのインタラクティブ描画には Plotly の WebGL（`scattergl`）を既定とし、
**DuckDB-Wasm + Canvas（ブラウザ側でDuckDBを実行し、生データに都度SQLを
投げる方式）は今は採用しない**。将来ニーズが変わったときの拡張候補として
判断根拠を残しておく。

| | WebGL（`scattergl`）採用 | DuckDB-Wasm + Canvas（不採用） |
| --- | --- | --- |
| 重い処理の場所 | Python側（DuckDB）で集計済みデータをHTMLに埋め込み、ブラウザは描画のみ | ブラウザ側でDuckDBを実行し、生Parquetに都度SQLを実行 |
| できること | パン・ズーム・ホバー・凡例トグルなど「見せ方の操作」 | グルーピング変更・再集計などの「問い直し（再クエリ）」 |
| 配布 | 自己完結HTML1枚、`file://`でそのまま開ける | wasm/JS/Parquet一式が必要。`file://`だとfetchがCORSでブロックされがちで簡易サーバーが要ることが多い |
| 実装コスト | `fig.write_html()`で完結。既存のPythonスタックのまま | JS/WASMのグルーコードを自前実装。技術スタックが増える |

**判断理由**: このプロジェクトは既に「`analyze.py`で可視化用に集計・サンプリング
してから`visualize.py`に渡す」設計にしている。この前提では、ブラウザは
軽量化済みデータをきれいに描画できればよく、`scattergl`で十分。DuckDB-Wasmが
活きるのは「事前集計をせず生データに対してブラウザ側でその場でクエリを
投げ直したい」という、今とは異なるユースケース（ミニBIツールに近いもの）で、
実装・配布の手間も一段重くなる。

**再検討する条件**: 「スクリプトを再実行せず、レポートを開いたままフィルタ条件を
変えて何度も掘り下げたい」というニーズが強くなったら、DuckDB-Wasm+Canvasへの
切り替えを検討する。

## 最重要ルール2: スクリプトには必ず説明資料を残す

`scripts/` 配下にスクリプトを**新規作成 or 内容を変更**したら、対応する
説明資料を `docs/<スクリプト名>.md`（例: `scripts/sales_summary.py` →
`docs/sales_summary.md`）として必ず作成・更新すること。テンプレートは
`docs/_template.md` を使う。

説明資料には最低限、次の3項目を含める。

1. **処理概要** — 何をするスクリプトか（何を読み、どう加工し、何を作るか）を
   短くまとめる。
2. **I/O説明** — 入力（ファイルパス・想定スキーマ・引数）と出力（ファイル・
   形式・内容）を具体的に書く。
3. **実行オプション** — コマンドライン引数・オプションと既定値、実行コマンド例。

コード側にもdocstring・`argparse`の`help`は書くが、それとは別に
`docs/*.md` に人が読む説明資料として残すことを省略しない。ドキュメントの
無いスクリプトを追加・変更したままにしない。

## ディレクトリ構成

```text
AnalyseTool/
├── CLAUDE.md            このファイル（プロジェクトルール）
├── README.md            プロジェクト概要
├── pyproject.toml       uv プロジェクト定義
├── scripts/             各ツールのエントリポイント（薄いラッパー）
├── docs/                各スクリプトの説明資料（scripts/ と1対1対応）
│   └── _template.md     説明資料のテンプレート
├── src/analyse_tool/
│   ├── common/
│   │   ├── charts/        グラフ種類ごとの共通モジュール（line.py/bar.py等）
│   │   └── profile.py     データ定義情報(プロファイル)の共通フォーマット
│   └── <tool_name>/      ツールごとのサブパッケージ（cli.py/io.py/prepare.py等）
├── profiles/            データ定義情報(プロファイル)のJSON（prepare.pyの出力 or 手書き）
├── data/                分析対象データ（git管理外・再取得/再生成前提）
└── output/              スクリプトの出力先（git管理外）
```

## 開発環境

- パッケージ管理は `uv`。依存追加は `uv add <パッケージ名>`。
- スクリプト実行は `uv run python scripts/<スクリプト名>.py [オプション]`。
- Python バージョンは `.python-version` に準拠。
- 可視化（`visualize.py`）でインタラクティブなレポートが必要な場合は
  `plotly` を標準ライブラリとする（初回使用時に `uv add plotly`）。
- 数百万〜数億行のデータ加工・プロファイリングは `duckdb` + `pyarrow`
  （Parquet）を標準とする（初回使用時に `uv add duckdb pyarrow`）。

## スクリプト作成時の進め方

0. 実データがまだ無い／直接使えない場合は、先に `generate_sample_data`
   （前述）でサンプルデータを作ってから開発を進める。
1. `src/analyse_tool/<ツール名>/` にサブパッケージを作り、`cli.py` /
   `io.py` に加えて `prepare.py`（前準備＝データ傾向の把握）/
   `process.py`（データ加工）/ `analyze.py`（分析）/
   `visualize.py`（可視化）の4ステップに分けて実装する。入出力パスや
   挙動は `argparse` などでオプション化し、決め打ちにしない。
2. `scripts/<ツール名>.py` にエントリポイントを置き、上記パッケージの
   `main()`（4ステップを順に呼ぶ）を呼び出すだけにする。
3. 同名で `docs/<ツール名>.md` を `docs/_template.md` から作成し、
   処理概要・I/O説明・実行オプションを埋める。
4. 新しい依存ライブラリを使ったら `uv add` で `pyproject.toml` /
   `uv.lock` に反映する。
5. 出力物は `output/` 配下に書き出す想定にする（git管理外）。
