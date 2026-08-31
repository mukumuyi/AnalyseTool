# 開発ガイドライン

## コーディング規約

- **リント/フォーマット**: コード変更後は必ず`uv run ruff check .`と
  `uv run ruff format .`を実行する（初回使用時に`uv add --dev ruff`）。
- **型チェック**: `uv run mypy .`を実行する（初回使用時に`uv add --dev mypy`）。
  公開関数の引数・戻り値には型ヒントを必ず付け、ファイル冒頭に
  `from __future__ import annotations`を書く。
- **依存の方向**: モジュール間の循環依存を禁止する。依存の方向は
  `docs/architecture.md`の「設計原則」に従う。
- **共通処理の置き場所**: 共通処理は`common/`に切り出し、各モジュールに
  重複実装しない。全プロジェクト横断の処理は`src/analyse_tool/common/`、
  特定プロジェクト内の複数ツールだけで使う処理は
  `src/analyse_tool/<プロジェクト名>/common/`に置く
  （`docs/repository-structure.md`参照）。特定ツール専用の処理は
  そのツールのサブパッケージ内に閉じる。
- **先回りして共通化しない（`visualize.py`肥大化対策）**: 各ツールの
  `visualize.py`は「どのグラフをどの段に、どんなパラメータで置くか」を
  決めるだけの薄い調整役に徹し、集計（`analyze.py`の責務）・描画
  （`common/charts/*`の責務）を持ち込まない。レポートのセクションごとに
  小さいプライベート関数（`_build_section1_xxx()`等）に分割し、
  1関数1セクションを保つ。**2つ以上のツールで同じ組み立てパターンが
  必要になって初めて**`common/`側への切り出しを検討する。1ツールしか
  使わない段階で`common/`に先回りして共通化しない（プロジェクトが増えても
  各`visualize.py`が際限なく肥大化しないようにするための方針）。
- **公開インターフェース**: 各サブパッケージが外部に公開する関数は、
  呼び出し元（`__init__.py`の`main()`や他モジュール）が直接使うものに
  限定する。内部実装専用の関数は先頭にアンダースコアを付ける
  （例: `_generate_id()`）。
- **SQLの書き方**: DuckDBのSQLは1関数=1つの完結したSELECT文とし、
  文字列結合による動的なSQL組み立て（条件によってSQL文自体を分岐生成
  する等）は避ける。値の埋め込みはテーブル名・列名等の識別子に限り、
  外部入力をそのままSQL文字列に埋め込まない（SQLインジェクション対策と、
  将来の`dbt`移行のしやすさの両方の理由。`docs/architecture.md`参照）。
- **HTMLレポートへのデータ埋め込み**: レポートHTMLにデータを埋め込む際は
  `common/report.py`の`_escape()`のようにHTMLエスケープを行い、埋め込んだ
  値が意図せずタグとして解釈されないようにする。
- **出力ファイルの安全な書き込み**: 出力ファイルへの書き込みは、一時ファイル
  に書いてから成功時のみ`os.replace()`等でリネームする。書き込み中に異常
  終了しても、壊れた（中途半端な）ファイルが残らないようにする（大量データ
  生成中のエラーを想定）。
- **ロギング**: 現状は`print()`による標準出力のみとする。ログレベル管理が
  必要になった場合は、モジュール単位で`logging.getLogger(__name__)`を
  取得する形に移行する。

## 命名規則

- **プロジェクト名・ツール名**: 英語のsnake_case（例:
  `customer_pref_summary`）。日本語名や略語だけの名前は避け、内容が
  推測できる名前にする。
- **Pythonの識別子**: モジュール・関数・変数名はPEP8に準拠したsnake_case、
  クラス名はPascalCase（例: `DatasetProfile`）。内部実装専用の関数・変数は
  先頭にアンダースコアを付ける（例: `_generate_numeric()`）。
- **ファイル・ディレクトリ**: `docs/repository-structure.md`の構成に従う
  （`profiles/<プロジェクト名>/<テーブル名>.json`、
  `docs/<プロジェクト名>/<ツール名>.md`等）。
- ドキュメントの見出し・説明文は日本語、コード上の識別子（変数名・関数名・
  クラス名）は英語で統一する。

## スタイリング規約

- フォーマットは`ruff format`に従い、個別に手動整形しない。
- docstringは日本語で、`Args:`/`Returns:`を使うGoogleスタイルに揃える
  （`src/analyse_tool/common/`配下の実装を参照）。
- 型ヒントを必須とし、`from __future__ import annotations`をファイル冒頭
  に置く（`X | None`のような新しい記法をPython 3.10でも使うため）。
- 1モジュール・1関数がやることは1つに絞る（`CLAUDE.md`の最重要ルール1を
  参照）。長くなってきたら早めに分割する。

## テスト規約

- テストフレームワークは**pytest**を採用する（`uv add --dev pytest`）。
  標準ライブラリの`unittest`より記述量が少なく、pandas/Plotlyのオブジェクト
  をそのまま`assert`で検証しやすいため。
- **「純粋な実装」（データを受け取り値を返すだけで、ファイルI/O・外部状態に
  依存しない関数）には必ずユニットテストを書く。** 対象の例:
  `common/charts/*.py`の各グラフ生成関数、`common/profile.py`の
  `DatasetProfile`/`ColumnProfile`まわり、`generate.py`の生成ロジック、
  `analyze.py`の集計関数。
- ファイルI/Oを伴う関数（`io.py`）は、必要に応じて一時ディレクトリ
  （pytestの`tmp_path`フィクスチャ）を使ったテストを書く。DuckDB/Parquet
  を介したテストも、小さいデータで可能な範囲で書く。
- テストは`tests/`配下に、`src/analyse_tool/`と対応する構成で置く
  （例: `src/analyse_tool/common/charts/bar.py` →
  `tests/common/charts/test_bar.py`）。
- 実行は`uv run pytest`。

## Git規約

ブランチ運用は **GitFlow** に従う。

| ブランチ | 役割 | 分岐元 | マージ先 |
| --- | --- | --- | --- |
| `main` | 常にリリース可能な状態を保つ本番ブランチ | - | - |
| `develop` | 開発中の最新コードを統合するブランチ | `main` | - |
| `feature/<名称>` | 機能開発用ブランチ | `develop` | `develop` |
| `release/<バージョン>` | リリース準備用ブランチ | `develop` | `main` と `develop` |
| `hotfix/<名称>` | 本番の緊急修正用ブランチ | `main` | `main` と `develop` |

- 通常の機能追加・修正は `feature/` ブランチを切って作業し、`develop` にマージする。
- リリース時は `develop` から `release/` ブランチを切り、動作確認後に `main`（タグ付け）と
  `develop` の両方へマージする。
- 本番障害の緊急修正は `main` から `hotfix/` ブランチを切り、修正後に `main` と `develop`
  の両方へマージする。
- **コミットの粒度**: 1コミットは`tasklist.md`の1タスク、または意味の
  まとまり1つに対応させる。無関係な変更を1コミットに混在させない。
- **コミットメッセージ**: 英語・命令形の1行要約（目安50文字程度）で
  「何をしたか」を書く（例:
  `Fix stage2 chart width bug in eqp_workload_analysis report`）。
  必要なら本文に理由・背景を補足する。
- **PRの粒度**: 1つの`.steering/[YYYYMMDD]-[開発タイトル]/`（作業単位）を
  1PRに対応させる。
