# リポジトリ構造定義書

## フォルダ・ファイル構成

```text
AnalyseTool/
├── CLAUDE.md                    プロジェクトルール（ドキュメント運用の定義）
├── README.md                    プロジェクト概要
├── pyproject.toml / uv.lock     uvプロジェクト定義
├── .python-version              Pythonバージョン固定
│
├── scripts/                     各ツールのエントリポイント（薄いラッパー）※本採用後に作成
│   └── <プロジェクト名>/
│       └── <ツール名>.py
├── src/analyse_tool/            ツール本体の実装 ※本採用後に作成
│   ├── common/                  全プロジェクト横断で共有する処理
│   │   ├── charts/              グラフ種類ごとの共通モジュール（bar.py等）
│   │   ├── profile.py           DatasetProfile / ColumnProfile の定義
│   │   └── report.py            クリック連動ドリルダウンHTMLの組み立て
│   └── <プロジェクト名>/        分析プロジェクト単位のまとまり（例: sales）
│       ├── common/              そのプロジェクト内の複数ツールだけで共有する処理（必要な場合のみ）
│       └── <ツール名>/          ツールごとのサブパッケージ（cli.py/io.py/prepare.py等）
│
├── profiles/                    データ定義情報（プロファイル）のJSON
│   └── <プロジェクト名>/
│       ├── customers.json
│       └── orders.json
├── data/                        分析対象データ（git管理外）
├── output/                      スクリプトの出力先（git管理外）
│   └── <プロジェクト名>/
│       ├── index.html           そのプロジェクトの生成物一覧（実行ごとにリンクを追記）
│       └── <YYYYMMDD>/          実行日
│           └── <HHMMSS>/        実行時刻（同日複数回実行しても上書きされない）
│               └── <ツール名>.html 等
│
├── docs/
│   ├── product-requirements.md  永続的ドキュメント（プロダクト要求）
│   ├── functional-design.md     永続的ドキュメント（機能設計）
│   ├── architecture.md          永続的ドキュメント（技術仕様）
│   ├── repository-structure.md  永続的ドキュメント（このファイル）
│   ├── development-guidelines.md 永続的ドキュメント（開発ガイドライン）
│   ├── development-process.md   永続的ドキュメント（開発プロセス手順）
│   ├── diagram-guidelines.md    永続的ドキュメント（図表記載ルール）
│   ├── glossary/                永続的ドキュメント（ユビキタス言語、プロジェクト単位に分割）
│   │   ├── common.md            プロジェクト横断の用語
│   │   └── <プロジェクト名>.md  プロジェクト固有の用語
│   ├── <プロジェクト名>/
│   │   └── <ツール名>.md        本採用後の各ツール説明資料（scripts/と1対1対応）
│   │
│   ├── templates/               各種テンプレートの置き場
│   │   ├── product-requirements.md 等  永続的ドキュメントの空テンプレート（見出しのみ）
│   │   └── tool-doc.md          ツール説明資料のテンプレート
│   └── ideas/                   ブレスト・試作アイデアのメモ（後述）
│
└── .steering/                   作業単位ドキュメント
    └── [YYYYMMDD]-[開発タイトル]/
        ├── requirements.md
        ├── design.md
        └── tasklist.md
```

## ディレクトリの役割

| ディレクトリ | 役割 |
| --- | --- |
| `scripts/<プロジェクト名>/` | 各ツールのエントリポイント。CLI引数解析と`main()`呼び出しのみの薄いラッパー |
| `src/analyse_tool/common/` | **全プロジェクト横断**で共有する処理（プロファイル定義、共通チャート、レポート組み立て） |
| `src/analyse_tool/<プロジェクト名>/common/` | そのプロジェクト内の複数ツールだけで共有する処理（無ければ作らない） |
| `src/analyse_tool/<プロジェクト名>/<ツール名>/` | ツールごとの実装（`cli.py`/`io.py`/`prepare.py`/`process.py`/`analyze.py`/`visualize.py`、または例外的な3モジュール構成） |
| `profiles/<プロジェクト名>/` | データ定義情報（プロファイル）のJSON。`prepare.py`の出力または手書き |
| `data/` | 分析対象データ（git管理外・再取得/再生成前提） |
| `output/<プロジェクト名>/` | スクリプトの出力先（git管理外）。`<YYYYMMDD>/<HHMMSS>/`配下に実行ごとの出力を残し、直下の`index.html`から一覧・リンクできるようにする |
| `docs/`（直下） | 永続的ドキュメント一式 |
| `docs/<プロジェクト名>/` | 本採用後の各ツール説明資料 |
| `docs/glossary/` | ユビキタス言語。全プロジェクト横断の用語（`common.md`）とプロジェクト固有の用語（`<プロジェクト名>.md`）に分ける |
| `docs/templates/` | テンプレートの置き場。永続的ドキュメントの空テンプレートとツール説明資料のテンプレート（`tool-doc.md`）をまとめる |
| `docs/ideas/` | ブレスト・試作アイデアのメモ（後述の「現在ideas/reference/にあるもの」を参照） |
| `.steering/` | 作業単位ドキュメント（今回の要求・設計・タスクリスト） |

「プロジェクト」の境界は、扱うデータ（テーブル群）と業務ドメインで決める
（例: 顧客・注文データを扱う分析群なら`sales`のようにまとめる）。現時点では
具体的なプロジェクトが1つも本採用されていないため、最初のツールを
`src/`+`scripts/`へ本採用するタイミングで最初のプロジェクト名を決める。

## ファイル配置ルール

### 新しいツールの作り方（通常のフロー）

`.steering/`で要求・設計を固めたうえで、直接
`src/analyse_tool/<プロジェクト名>/<ツール名>/` + `scripts/<プロジェクト名>/<ツール名>.py`
として実装する。`docs/ideas/`や`docs/reference/`を経由することは通常は不要。

### 現在`docs/ideas/`にあるもの（移行期の一時的な状態）

`docs/ideas/`には、現在のドキュメント体系に再構成する前のブレストメモ・
試作アイデア（`MEMO.md`/`MEMO2.md`）が記録として残っている。これは今回の
仕切り直しに伴う一時的な保管であり、新規ツール開発で必ず経由する標準の
場所ではない。

現在この配下にあった試作実装（`customer_pref_summary`・
`generate_sample_data`）は`docs/reference/`へ移動済みで、最初の本採用
（`src/`+`scripts/`への移行）が完了したら、`docs/reference/`ごと削除する
想定。

### `output/`の構成

`output/`直下がフラットに散らかるのを防ぐため、実行ごとの出力は
`output/<プロジェクト名>/<YYYYMMDD>/<HHMMSS>/`配下に書き出す（同日に
複数回実行しても上書きされず、実行履歴が残る）。

`output/<プロジェクト名>/index.html`は、そのプロジェクトの生成物の目次
（実行日時・ツール名と、各`<YYYYMMDD>/<HHMMSS>/`配下のレポートへの
リンクの一覧）で、`file://`で開いてそのままブラウザ遷移で辿れるように
する。実行のたびに新しいエントリを追記して更新する。

この追記・更新処理は各ツールの`io.py`が個別に実装するのではなく、
`src/analyse_tool/common/`に共通ヘルパー（例:
`output_index.py`の`register_output()`）を置き、各ツールの`io.py`が
レポート等を書き出した後にこれを呼び出す形にする（`docs/functional-design.md`
の「コンポーネント設計」を参照）。

### ドキュメントの置き場所

- 永続的ドキュメント（`docs/product-requirements.md`等）を新規作成する際は、
  `docs/templates/`の対応する空テンプレートを複製して書き始める。
- ツール説明資料（`docs/<プロジェクト名>/<ツール名>.md`）を新規作成する際は、
  `docs/templates/tool-doc.md`を複製して書き始める。
- 作業単位ドキュメント（`.steering/`）は`docs/development-process.md`の
  命名規則・手順に従う。

### その他

- `common/`配下に置くのは複数ツールで共有する処理のみ。特定ツール専用の
  処理はそのツールのサブパッケージ側に置く。
- `data/`・`output/`はgit管理外（`.gitignore`）。再取得・再生成できない
  ものは置かない。空のディレクトリ自体をgit管理下に残したい場合は
  `.gitkeep`を置く。
- ファイル・ディレクトリの命名規則（英語表記・スネークケース等）の詳細は
  `docs/development-guidelines.md`の「命名規則」で定める。
- `tests/`の配置ルールは、`docs/development-guidelines.md`のテスト規約と
  合わせて着手時に定める。
