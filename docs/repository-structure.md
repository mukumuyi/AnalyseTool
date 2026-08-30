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
│   └── <ツール名>.py
├── src/analyse_tool/            ツール本体の実装 ※本採用後に作成
│   ├── common/                  複数ツールで共有する処理
│   │   ├── charts/              グラフ種類ごとの共通モジュール（bar.py等）
│   │   ├── profile.py           DatasetProfile / ColumnProfile の定義
│   │   └── report.py            クリック連動ドリルダウンHTMLの組み立て
│   └── <ツール名>/              ツールごとのサブパッケージ（cli.py/io.py/prepare.py等）
│
├── profiles/                    データ定義情報（プロファイル）のJSON
├── data/                        分析対象データ（git管理外）
├── output/                      スクリプトの出力先（git管理外）
│
├── docs/
│   ├── product-requirements.md  永続的ドキュメント（プロダクト要求）
│   ├── functional-design.md     永続的ドキュメント（機能設計）
│   ├── architecture.md          永続的ドキュメント（技術仕様）
│   ├── repository-structure.md  永続的ドキュメント（このファイル）
│   ├── development-guidelines.md 永続的ドキュメント（開発ガイドライン）
│   ├── development-process.md   永続的ドキュメント（開発プロセス手順）
│   ├── diagram-guidelines.md    永続的ドキュメント（図表記載ルール）
│   ├── glossary.md              永続的ドキュメント（ユビキタス言語）
│   ├── <ツール名>.md            本採用後の各ツール説明資料（scripts/と1対1対応）
│   │
│   ├── templates/               各種テンプレートの置き場
│   │   ├── product-requirements.md 等  永続的ドキュメントの空テンプレート（見出しのみ）
│   │   └── tool-doc.md          ツール説明資料（docs/<ツール名>.md）のテンプレート
│   ├── ideas/                   実装アイデア・ブレストメモの置き場（動作確認前でもよい）
│   └── reference/                動作確認まで済んだリファレンス実装の置き場
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
| `scripts/` | 各ツールのエントリポイント。CLI引数解析と`main()`呼び出しのみの薄いラッパー |
| `src/analyse_tool/common/` | 複数ツールで共有する処理（プロファイル定義、共通チャート、レポート組み立て） |
| `src/analyse_tool/<ツール名>/` | ツールごとの実装（`cli.py`/`io.py`/`prepare.py`/`process.py`/`analyze.py`/`visualize.py`、または例外的な3モジュール構成） |
| `profiles/` | データ定義情報（プロファイル）のJSON。`prepare.py`の出力または手書き |
| `data/` | 分析対象データ（git管理外・再取得/再生成前提） |
| `output/` | スクリプトの出力先（git管理外） |
| `docs/`（直下） | 永続的ドキュメント一式、および本採用後の各ツール説明資料 |
| `docs/templates/` | テンプレートの置き場。永続的ドキュメントの空テンプレート（見出しのみの状態を保管し、新規プロジェクトや作り直し時の原本にする）と、ツール説明資料のテンプレート（`tool-doc.md`）をまとめる |
| `docs/ideas/` | まだ動作確認前の実装アイデア・ブレストメモの置き場 |
| `docs/reference/` | 動作確認まで済んだが`src/`・`scripts/`へはまだ昇格していないリファレンス実装の置き場。`customer_pref_summary`・`generate_sample_data`は現在この段階 |
| `.steering/` | 作業単位ドキュメント（今回の要求・設計・タスクリスト） |

## ファイル配置ルール

### 新しいツールを作るときの3段階

1. **`docs/ideas/`**: アイデア段階。動作未確認のメモ・下書きでよい。
2. **`docs/reference/`**: 動作確認まで済んだ実装。まだ`src/`・`scripts/`には
   昇格していない（`analyse_tool/<ツール名>/`と`<ツール名>.py`をこの直下に
   置く。`src/`/`scripts/`のサブディレクトリには分けない）。
3. **`src/analyse_tool/<ツール名>/` + `scripts/<ツール名>.py`**: 本採用。
   ユーザーからの指示（当面は直接指定、その後は`.steering/`経由）を受けて
   `docs/reference/`から昇格させる。

### ドキュメントの置き場所

- 永続的ドキュメント（`docs/product-requirements.md`等）を新規作成する際は、
  `docs/templates/`の対応する空テンプレートを複製して書き始める。
- ツール説明資料（`docs/<ツール名>.md`）を新規作成する際は、
  `docs/templates/tool-doc.md`を複製して書き始める。
- 作業単位ドキュメント（`.steering/`）は`docs/development-process.md`の
  命名規則・手順に従う。

### その他

- `common/`配下に置くのは複数ツールで共有する処理のみ。特定ツール専用の
  処理はそのツールのサブパッケージ側に置く。
- `data/`・`output/`はgit管理外（`.gitignore`）。再取得・再生成できない
  ものは置かない。
