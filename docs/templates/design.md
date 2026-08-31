# design.md — <開発タイトル>の設計

## 対象

### 構成物一覧

今回の作業で新規作成・変更する構成物を一覧にする。次のルールを守る。

- **1オブジェクト1行**で書く。`{a,b,c}.py`のようなまとめ書きはしない
  （ファイルごとに行を分ける）
- **グラフは対象外**にする。グラフの種類・見せ方は要求仕様
  （`requirements.md`・本ファイルの「画面レイアウト」）側の対象であり、
  ここに書くとコードの行と重複する
- **種別は英語3文字**で統一する（例: `SCR`=画面、`SRC`=コード、
  `DAT`=データ、`DOC`=ドキュメント）。ドキュメントが縦長になりすぎるのを
  防ぐため

| 種別 | 名称 | 対応種別 | 内容 |
| --- | --- | --- | --- |
| SCR | AAA | 新 | 〇〇の結合する |
| SRC | BBB.py | 変 | 2段だったのを3段に変更 |
| DAT | CCC | 変 | 2段だったのを3段に変更 |
| DOC | docs/xxx.md | 変 | 〇〇の記載を追加 |

## 画面レイアウト

可視化を含む場合、確定版の画面配置（モックのスクリーンショット・
Artifactへのリンク・ワイヤーフレーム等）をここに置く。

## 画面遷移図

クリック等の操作でどの画面・グラフに遷移するか（ドリルダウンの段数、
何をクリックすると何が起きるか）を図で示す。

## 機能別処理フロー

モジュール（`prepare.py`/`process.py`/`analyze.py`/`visualize.py`等）
ごとに、処理順序を表すアクティビティ図をMermaidで書く。1モジュール
1図を基本とし、大きくなる場合のみ分割する。呼び出し関係（import の
方向）は表さない（それは「コンポーネント構成図」の役割）。表記方法は
`docs/diagram-guidelines.md`の「アクティビティ図（処理順序図）の
描き方」に従う。

```mermaid
flowchart TD
    subgraph SW1["prepare.py（EDA）"]
        Start1((開始)) -->
        RawData1[("RawData <br/> proc_history")] -->
        Check("データ内の各項目の統計値算出 <br/> カテゴリの種類と出現率算出") -->
        ProfileData["ProfileData <br/> proc_history(json)"] -->
        End1((終了))
    end
```

## コンポーネント構成図

モジュール間の依存関係（import する方向）をMermaidで書く。共通処理
（`common/`）とツール固有コードの境界、層構造を採る場合はその層の
上下関係が分かるようにする。

```mermaid
flowchart TD
    subgraph L3["案件固有: trial_factory/eqp_workload_analysis/"]
        vis["visualize.py<br/>レポート全体の調整・グラフ配置・<br/>部品へのパラメータ受け渡し"]
    end

    subgraph L2["第2層＝分析の型: common/charts/"]
        pareto["pareto.py<br/>(降順ソート・累積構成比・80%線)"]
        twograph["twograph.py<br/>(x軸共有の2段組)"]
    end

    subgraph L1["第1層＝見た目の型: common/charts/"]
        barline["barline.py<br/>(棒 + 第2軸の折れ線)"]
        bar["bar.py<br/>(積み上げ棒・既存＋単色モード追加)"]
        area["area.py<br/>(積み上げ面・階段状可)"]
        gantt["gantt.py<br/>(区間の水平棒)"]
        scatter["scatter.py<br/>(散布図・scattergl固定)"]
    end

    subgraph SH["ドリルダウン機構: common/"]
        report["report.py<br/>(N段クリック連動の組み立て)"]
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

## 課題対応

設計中に判明した課題・懸念点と、それぞれへの対応（結論）を書く。
経緯（誰が指摘したか等）ではなく、結論と根拠だけを残す。

## 残課題

`tasklist.md`着手前に確認・決定しておきたい未確定事項を列挙する。
