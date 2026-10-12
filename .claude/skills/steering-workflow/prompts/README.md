# サブエージェントに渡す指示文

`docs/development-process.md` の要件の独立確認・受け入れテスト作成・独立レビュー①〜③で、
作業セッションが Agent ツール（`subagent_type: general-purpose`）を起動するときに使う。

使い方：該当ファイルの本文を読み、`{{...}}` を実際のパス等に置き換えて、そのまま prompt に渡す。
**指示文と成果物のパス以外（経緯の説明・会話の要約・「たぶん大丈夫」等の見立て）は足さない。**

| ファイル | 使う場面 |
| --- | --- |
| `requirements-check.md` | 要件の独立確認（承認①の前） |
| `design-review.md` | 独立レビュー①（design.md 完成時） |
| `tasklist-review.md` | 独立レビュー②（tasklist.md 完成時） |
| `test-writer.md` | 受け入れテストの作成（実装の前）、テストの修正依頼 |
| `impl-review.md` | 独立レビュー③（実装・テスト完了時） |
