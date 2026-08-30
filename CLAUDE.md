# CLAUDE.md（プロジェクトメモリ）

## 概要
開発を進めるうえで遵守すべき標準ルールを定義します。

## プロジェクト構造
本リポジトリは、データ分析ツール専用のリポジトリです。

## ドキュメントの分類

### 1. 永続的ドキュメント（`docs/`）
アプリケーション全体の「何を作るか」「どう作るか」を定義する恒久的なドキュメント。
基本設計や方針が変わらない限り更新しません。プロジェクト全体の「北極星」として機能します。

| ファイル | 役割 |
| --- | --- |
| `docs/product-requirements.md` | プロダクト要求定義書 |
| `docs/functional-design.md` | 機能設計書 |
| `docs/architecture.md` | 技術仕様書 |
| `docs/repository-structure.md` | リポジトリ構造定義書 |
| `docs/development-guidelines.md` | 開発ガイドライン |
| `docs/diagram-guidelines.md` | 図表・ダイアグラムガイドライン |
| `docs/glossary/` | ユビキタス言語定義（`common.md`＝横断用語、`<プロジェクト名>.md`＝プロジェクト固有用語） |

各ファイルに何を書くかは、そのファイル冒頭の見出し構成に従います。

### 2. 作業単位ドキュメント（`.steering/`）
特定の開発作業における「今回何をするか」を定義する一時的なドキュメント。
作業ごとに新しいディレクトリを作成し、完了後は履歴として保持します。

```
.steering/[YYYYMMDD]-[開発タイトル]/
├── requirements.md   # 今回の作業の要求内容
├── design.md         # 変更内容の設計
└── tasklist.md       # タスクリストと進捗
```

例: `.steering/20250115-add-tag-feature/`

命名規則・作成手順の詳細は `docs/development-process.md` を参照。

## 開発の進め方

- 新規セットアップ時: `docs/development-process.md` の「初回セットアップ時の手順」に従う
- 機能追加・修正時: `docs/development-process.md` の「機能追加・修正時の手順」に従う
- 図表・ダイアグラムを書く際: `docs/diagram-guidelines.md` を参照

## 注意事項

- ドキュメントは1ファイルごとに作成し、**必ず確認・承認を得てから次に進む**
- 永続的ドキュメントと作業単位ドキュメントを混同しない
- `.steering/` のディレクトリ名は日付と開発タイトルで明確に識別できるようにする
- コーディング規約・スタイリング規約・テスト規約・Git規約の詳細は `docs/development-guidelines.md` を参照
