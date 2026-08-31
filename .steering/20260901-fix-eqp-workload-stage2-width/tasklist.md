# tasklist.md — ⑥-2装置稼働グラフの表示幅不整合バグ修正

`design.md`（承認済み）に基づく実装タスク。上から順に進める。

## タスク

- [x] 1. `src/analyse_tool/common/report.py`の`_MULTI_STAGE_TEMPLATE`内、
      段1（パレート図）クリックハンドラを修正する。対象の`.stage2-fig`を
      `display:block`にする際、その中の`.plotly-graph-div`に対して
      `Plotly.Plots.resize()`を呼ぶ処理を追加する（design.mdの
      「機能別処理フロー」の通り。`display:none`にする側へは呼ばない）
- [x] 2. `tests/common/test_report.py`に、段1クリックハンドラの生成JSへ
      `Plotly.Plots.resize`呼び出しが含まれることを確認するテストケースを
      追加する
- [x] 3. 品質チェックを実行する
      - `uv run ruff check .`: パス
      - `uv run ruff format .`: `report.py`・`test_report.py`は整形済み。
        `docs/reference/`配下4ファイルにも整形差分が出たが、本タスクの
        変更対象外（design.mdの構成物一覧に無い）の既存ファイルのため
        元に戻した（本タスクのスコープ外の既存フォーマット崩れ）
      - `uv run mypy .`: `src/analyse_tool/__init__.py`と
        `docs/reference/analyse_tool/__init__.py`が同名モジュールとして
        重複するエラーで全体が止まる。これは本タスクの変更と無関係の
        既存事象であることを`git stash`で変更前の状態に戻して再現・確認
        済み（対応は本タスクのスコープ外）。`--exclude 'docs/reference'`を
        付けて変更対象のみ検証したところ36ファイルすべてエラー無し
        （`report.py`の変更は文字列テンプレートの中身のみで型定義に
        影響しないため、想定通り）
      - `uv run pytest`: 53件全件パス（新規テスト含む）
- [x] 4. `requirements.md`の受け入れ条件を満たしているか最終確認した
      （下記「最終確認」を参照）

## 最終確認（requirements.mdの受け入れ条件との対応）

- ⑥-1パレート図で任意の設備をクリックしたとき、⑥-2の描画幅が初期選択
  設備と同じになること → 達成。表示切り替え直後に対象の
  `.plotly-graph-div`へ`Plotly.Plots.resize()`を呼ぶことで、
  `display:none`のまま確定していた誤ったサイズを再計算させる
- 設備の切り替えを繰り返しても毎回正しい幅で表示されること → 達成。
  クリックのたびに毎回同じ処理が実行されるため、どの順で選び直しても
  同じ結果になる
- 修正が`common/report.py`の該当箇所に閉じ、他のレポート要素へ影響しない
  こと → 達成。変更は段1クリックハンドラ内のみで、①〜⑤・⑥-1本体・
  ⑥-3・⑥-4（構築式側）のコードは未変更。既存の全53テストがパス
  していることでも裏付け
- 既存のユニット・結合テストが通ること → 達成（`uv run pytest`53件パス）

## 完了条件

- 上記タスクが全て完了していること → 完了
- `tests/common/test_report.py`の新規テストを含め、`uv run pytest`が
  全件パスすること → 確認済み（53 passed）
- `ruff check`・`mypy`が新規変更箇所についてエラー無しで通ること →
  確認済み（`mypy`は前述の通り既存の無関係な事象を除外して確認）

## 進捗状況

全タスク完了。

