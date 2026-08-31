# 開発プロセス

CLAUDE.md から参照される詳細手順。作業開始時に該当セクションを読むこと。

## `.steering/` ディレクトリの命名規則

```
.steering/[YYYYMMDD]-[開発タイトル]/
```

**例:**
- `.steering/20250103-initial-implementation/`
- `.steering/20250115-add-tag-feature/`
- `.steering/20250120-fix-filter-bug/`
- `.steering/20250201-improve-performance/`

## 初回セットアップ時の手順

### 1. フォルダ作成
```bash
mkdir -p docs
mkdir -p .steering
```

### 2. 永続的ドキュメント作成（`docs/`）

アプリケーション全体の設計を定義します。
各ドキュメントを作成後、必ず確認・承認を得てから次に進みます。

1. `docs/product-requirements.md` - プロダクト要求定義書
2. `docs/functional-design.md` - 機能設計書
3. `docs/architecture.md` - 技術仕様書
4. `docs/repository-structure.md` - リポジトリ構造定義書
5. `docs/development-guidelines.md` - 開発ガイドライン
6. `docs/diagram-guidelines.md` - 図表・ダイアグラムガイドライン
7. `docs/glossary/common.md` - ユビキタス言語定義（プロジェクト横断の用語）

**重要:** 1ファイルごとに作成後、必ず確認・承認を得てから次のファイル作成を行う

### 3. 初回実装用のステアリングファイル作成

初回実装用のディレクトリを作成し、実装に必要なドキュメントを配置します。

```bash
mkdir -p .steering/[YYYYMMDD]-initial-implementation
```

作成するドキュメント:
1. `.steering/[YYYYMMDD]-initial-implementation/requirements.md` - 初回実装の要求
2. `.steering/[YYYYMMDD]-initial-implementation/design.md` - 実装設計
3. `.steering/[YYYYMMDD]-initial-implementation/tasklist.md` - 実装タスク

### 4. 環境セットアップ
内容は「環境セットアップの内容」を参照。

### 5. 実装開始

`.steering/[YYYYMMDD]-initial-implementation/tasklist.md` に基づいて実装を進めます。

### 6. 品質チェック
内容は「品質チェックの内容」を参照。

## 機能追加・修正時の手順

### 1. 影響分析

- 永続的ドキュメント（`docs/`）への影響を確認
- 変更が基本設計に影響する場合は `docs/` を更新

### 2. ステアリングディレクトリ作成

```bash
mkdir -p .steering/[YYYYMMDD]-[開発タイトル]
```

**例:**
```bash
mkdir -p .steering/20250115-add-tag-feature
```

### 3. 作業単位ドキュメント作成

各ドキュメント作成後、必ず確認・承認を得てから次に進みます。

1. `.steering/[YYYYMMDD]-[開発タイトル]/requirements.md` - 要求内容
2. `.steering/[YYYYMMDD]-[開発タイトル]/design.md` - 設計
3. `.steering/[YYYYMMDD]-[開発タイトル]/tasklist.md` - タスクリスト

**重要:** 1ファイルごとに作成後、必ず確認・承認を得てから次のファイル作成を行う

**可視化（グラフ・レポート画面）を含む場合:**
文章だけでは画面の出来上がりが共有できず、実装後に「思っていたものと違う」
「グラフが密集して読めない」が判明して手戻りになる。そのため、
**上記1・2の承認を取る際に、画面を目で見られる形にして添える**こと。
静的なモックHTMLやダミーデータで描いたグラフなど、実物に近いものを示す。

- `requirements.md` の承認 ← ラフな画面イメージを添える
- `design.md` の承認 ← 確定版の画面配置・各グラフの見せ方を添える

**承認の回数は増やさない。** 追加の承認ステップを設けるのではなく、
既存の3回の承認のうち1・2を「文章だけで通さない」ようにするもの。

各ファイルに何を書くかは「作業単位ドキュメントの記載内容」を参照。

### 4. 永続的ドキュメント更新（必要な場合のみ）

変更が基本設計に影響する場合、該当する `docs/` 内のドキュメントを更新します。

### 5. 実装開始

`.steering/[YYYYMMDD]-[開発タイトル]/tasklist.md` に基づいて実装を進めます。

### 6. 品質チェック
内容は「品質チェックの内容」を参照。

## 作業単位ドキュメントの記載内容

### requirements.md
- 変更・追加する機能の説明
- ユーザーストーリー
- 受け入れ条件
- 制約事項
- **画面イメージ（ラフ）** — 可視化を含む場合のみ。「どんな画面が欲しいか」を
  絵で共有する段階。どのグラフを何枚、どんな順で置きたいか、どこを操作すると
  何が起きるか。この時点では手描き相当のラフでよく、細部は `design.md` で詰める

### design.md
`docs/templates/design.md`を複製して書き始める。テンプレートの構成:
- **対象／構成物一覧** — 今回新規作成・変更する構成物（画面・コード・
  データ・ドキュメント）を1オブジェクト1行で一覧にする（グラフの種類・
  見せ方は対象外。`requirements.md`・画面レイアウトの領分）。種別は
  英語3文字（`SCR`/`SRC`/`DAT`/`DOC`等）で統一する
- **画面レイアウト** — 可視化を含む場合のみ。`requirements.md` のラフを、
  技術的な制約（データ量・描画性能・HTMLサイズ等）を踏まえて確定させた
  もの。グラフ種類、縦横軸に何を取るか、色分けの意味、初期表示の範囲、
  凡例・ホバーで何を出すかも含む。**「全期間・全件を初期表示すると読めるか」
  は必ず検討する**（時間刻みの系列や多カテゴリの棒グラフは、全部出すと
  密集して読めなくなりやすい）
- **画面遷移図** — 可視化を含む場合のみ。クリック等の操作で何が起きるか
  （ドリルダウンの段数等）
- **機能別処理フロー** — モジュールごとの処理順序（アクティビティ図。
  書き方は `docs/diagram-guidelines.md` 参照）
- **コンポーネント構成図** — モジュール間の依存関係（importの方向）
- **課題対応** — 設計中に判明した課題・懸念点と、それぞれへの結論
  （経緯ではなく結論と根拠を書く）
- **残課題** — `tasklist.md`着手前に確認・決定しておきたい未確定事項

### tasklist.md
- 具体的な実装タスク
- タスクの進捗状況
- 完了条件
- 各タスク完了時の実施結果（品質チェックの結果、判明した問題があれば
  その原因切り分け・対応）
- 完了条件を requirements.md の受け入れ条件と突き合わせた最終確認
- 次回以降への申し送り事項（今回スコープ外にした課題、保留にした判断など。
  無ければ「特になし」と明記する）

## 環境セットアップの内容

```bash
uv sync                 # 依存をインストール
uv add <パッケージ名>    # 依存を追加（開発専用は uv add --dev）
```

- 実行は `uv run python scripts/<プロジェクト名>/<ツール名>.py`。
- Pythonバージョンは `.python-version` に準拠する。

## 品質チェックの内容

```bash
uv run ruff check .
uv run ruff format .
uv run mypy .
uv run pytest
```

- `pytest` はユニットテストに加え、必要に応じて結合テストも実行する。
  対象がファイルI/OやDuckDB/Parquetを介する処理であれば、`tests/` 配下に
  結合的な検証も書く。
- 対象ツールが本採用（継続利用する）ツールの場合、
  `docs/<プロジェクト名>/<ツール名>.md` を作成・更新する（新規作成時は
  `docs/templates/tool-doc.md` を複製。`scripts/` と1対1対応）。実験的な
  使い捨てツールの場合は不要。
- 最後に、実装内容が `requirements.md` の受け入れ条件を満たしているか見直す。
