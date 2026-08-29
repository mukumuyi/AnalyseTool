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
6. `docs/glossary.md` - ユビキタス言語定義

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

### design.md
- 実装アプローチ
- 変更するコンポーネント
- データ構造の変更
- 影響範囲の分析

### tasklist.md
- 具体的な実装タスク
- タスクの進捗状況
- 完了条件

## 環境セットアップの内容

- 必要な依存パッケージをインストールする（例: `npm install`）
- `.env` 等の環境変数を設定する
- ローカル環境でアプリケーションが起動することを確認する

## 品質チェックの内容

- Lintを実行し、エラーがないことを確認する
- 型チェックを実行する
- テストを実行する（ユニットテスト、必要に応じて結合テスト）
- 対象機能が requirements.md の受け入れ条件を満たしているか確認する
