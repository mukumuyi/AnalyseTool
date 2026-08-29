"""analyse_tool: scripts/ 配下のスクリプトから共有する共通処理を置く場所。

現時点では中身は無い。複数スクリプトで重複するI/O処理・共通ロジックが
出てきたら、ここに関数を切り出して `from analyse_tool.xxx import ...` の形で
scripts/ から読み込む。
"""
