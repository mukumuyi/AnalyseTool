# 機能設計書

## 機能ごとのアーキテクチャ

各分析ツールは、`prepare`（前準備/EDA）→`process`（データ加工）→`analyze`
（分析）→`visualize`（可視化）の4ステップに分割する。ステップ間は「データを
受け取り、加工済みのデータを返す」関数として繋がり、互いの実装を意識しない。

```mermaid
flowchart LR
    A[生データ<br/>Parquet] --> B["① prepare<br/>(EDA: 傾向把握)"]
    B -->|DatasetProfile| C["② process<br/>(クレンジング/加工)"]
    C -->|DuckDBリレーション| D["③ analyze<br/>(集計・サンプリング)"]
    D -->|集計済みの小さいデータ| E["④ visualize<br/>(グラフ+レポート組み立て)"]
    E --> F[レポートHTML<br/>output/プロジェクト名/日付/]
    B -.->|profile.json| G[(profiles/プロジェクト名/)]
```

例外として、`generate_sample_data`のように実データを分析するのではなく
「データそのものを作る」ツールは、この4ステップに強引に当てはめず
`cli.py`/`io.py`/生成ロジック本体、という3モジュール構成にする
(対象範囲は`docs/product-requirements.md`、命名規則は`docs/repository-structure.md`
を参照)。

## システム構成図

サーバーを持たないローカル完結のCLIツール群。ネットワーク通信は行わない。

```mermaid
flowchart LR
    U[利用者] -->|"uv run python scripts/*.py"| S[分析ツール<br/>Python/DuckDB]
    S -->|読み込み| P[(data/プロジェクト名/ or<br/>output/プロジェクト名/<br/>Parquet)]
    S -->|書き出し| O[(output/プロジェクト名/日付/<br/>レポートHTML・profile.json)]
    U -->|file://で開く| O
```

- 将来`dbt`を導入した場合も、dbtはDuckDB上のSQL変換層として組み込む想定で、
  外部公開するAPI・サーバーは持たない（システム構成自体は変わらない）。

## データモデル定義（ER図含む）

### プロファイル（`DatasetProfile`/`ColumnProfile`）

分析対象データの「傾向」を表す共通フォーマット。`prepare.py`（実データから
`profile_from_parquet()`で自動生成）と`generate_sample_data`（プロファイルを
入力にサンプルデータを生成）の間の共通契約になっている。

```mermaid
classDiagram
    class DatasetProfile {
        +string name
        +int row_count
        +ColumnProfile[] columns
    }
    class ColumnProfile {
        +string name
        +string dtype
        +Role role
        +float null_rate
        +float min
        +float max
        +float mean
        +float stddev
        +string distribution
        +CategoryFreq[] categories
        +float true_rate
        +ColumnReference references
    }
    class ColumnReference {
        +string table
        +string column
    }
    class CategoryFreq {
        +string value
        +float freq
    }
    class Role {
        <<enumeration>>
        id
        numeric
        categorical
        date
        boolean
    }
    DatasetProfile "1" *-- "N" ColumnProfile
    ColumnProfile "1" o-- "N" CategoryFreq
    ColumnProfile "0..1" o-- "1" ColumnReference : references
    ColumnProfile --> Role
```

現状は**単一テーブル前提**（`profiles/<プロジェクト名>/customers.json`、
`profiles/<プロジェクト名>/orders.json`のように、テーブルごとに独立した
プロファイル）。これに対し、`ColumnProfile`に
他テーブルの列を指す`references`（`ColumnReference{table, column}`）を追加し、
外部キーに相当する関係を**プロファイル上では定義できる**ようにする（例:
`orders.customer_id`に`references: {table: "customers", column: "customer_id"}`
を設定する）。

**今回のスコープ**: この定義を**サンプルデータ生成が考慮する**（参照先テーブル
の生成結果から値を選ぶ等、実態に近いデータを作る）ところまでを対象とし、生成後
に参照整合性を検証・保証する（全件が実在するかを確認する）ところまでは対象外
とする（`docs/product-requirements.md`の「今後の拡張予定」を参照）。

この対応により、`generate_sample_data`は現状の「プロファイル1つ→Parquet1つ」
という単純な1:1変換ではなく、**依存関係のあるプロファイル群をまとめて受け取り、
参照先→参照元の順で生成する**形に拡張する必要がある（具体的なCLI・入出力の形
は実装時に設計する）。

```mermaid
erDiagram
    customers ||--o{ orders : "customer_id (referencesで定義・生成時に考慮、整合性は未保証)"
    customers {
        string customer_id
        string customer_name
        string segment
        string pref
    }
    orders {
        string order_id
        string customer_id
        date order_date
        float amount
    }
```

## コンポーネント設計

### 共通コンポーネント（`common/`）

| モジュール | 役割 | 状態 |
| --- | --- | --- |
| `common/profile.py` | `DatasetProfile`/`ColumnProfile`の定義、保存・読込、`profile_from_parquet()` | 実装済み |
| `common/report.py` | グラフ＋クリック連動明細表をまとめた自己完結HTMLの組み立て | 実装済み（1段ドリルダウンのみ） |
| `common/output_index.py` | `output/<プロジェクト名>/index.html`への実行結果の登録・追記（`register_output()`）。各ツールの`io.py`がレポート書き出し後に呼び出す | 未実装（設計合意済み） |
| `common/charts/bar.py` | 積み上げ棒グラフ | 実装済み |
| `common/charts/box.py` | 箱ひげ図（EDAでの分布・外れ値確認） | 未実装（設計合意済み） |
| `common/charts/histogram.py` | ヒストグラム（EDAでの分布形状確認、`color`で重ね描き） | 未実装（設計合意済み） |
| `common/charts/pie.py` | 円グラフ（構成比） | 未実装（設計合意済み） |
| `common/charts/scatter.py` | 散布図（`scattergl`固定、WebGL） | 未実装（設計合意済み） |
| `common/charts/pareto.py` | パレート図（棒+累積構成比の二軸、独立モジュール） | 未実装（設計合意済み） |
| `common/charts/timeline.py` | ガントチャート（期間の横棒） | 未実装（設計合意済み） |

### `common/report.py`のドリルダウン設計方針

現状の`build_bar_click_detail_html()`は「棒グラフの1クリック→フラットな
明細表」という1段専用の構造（`detail_match_columns`が固定2キーの辞書）。
2段目のドリルダウン（グラフ→グラフ→明細）に拡張する可能性を見据え、将来
書き換える際は次の方針を採る。

- クリック条件を固定2キーの辞書ではなく、**フィルタ条件のリスト**として
  持たせる（例: `[{"column": "pref", "match": "x"}, {"column": "segment", "match": "trace_name"}]`）。
- 段数はこのリストの長さで決まり、最終段は必ず明細表、それ以外の段は
  グラフとする。
- 2段目以降の集計（グラフ描画用のgroup by/count）は、埋め込み済みの明細
  データに対してブラウザ側JSで行う（Pythonでの再集計はクリック時には
  発生しないため）。単純な件数集計に限定し、JS側の複雑化を避ける。

### ツールごとの実装（`docs/reference/`に参考実装あり）

| ツール | 構成 | 備考 |
| --- | --- | --- |
| `generate_sample_data` | `cli.py`/`io.py`/`generate.py`（4ステップ構成の例外） | プロファイルJSON→Parquetを`CHUNK_ROWS`単位で生成。`references`対応時は、依存関係のあるプロファイル群をまとめて受け取り参照先→参照元の順で生成する形への拡張が必要（未実装、上記「データモデル定義」参照） |
| `customer_pref_summary` | `cli.py`/`io.py`/`prepare.py`/`process.py`/`analyze.py`/`visualize.py` | pref×segment集計＋クリック連動明細のリファレンス実装 |

## ユースケース図、画面遷移図、ワイヤフレーム

従来のUIを持たないため、「レポートHTMLの操作フロー」として記載する。

```mermaid
flowchart TD
    A[レポートHTMLをfile://で開く] --> B[集計グラフを閲覧<br/>ズーム・ホバー・凡例トグル]
    B --> C{気になる棒をクリック}
    C -->|1段目| D[明細データが下に表示される<br/>最大2000行、超過時は注記]
    C -->|将来: 2段目に拡張時| E[次の粒度の集計グラフを表示]
    E --> F{さらにクリック}
    F --> D
```

## API設計（将来的にバックエンドと連携する場合）

現時点ではAPI・バックエンドを持たない（対象外）。将来`dbt`を導入しても、
dbtはDuckDB上のSQL変換層であり、外部公開するAPIではないため、当面は
本セクションの対象外のまま据え置く。
