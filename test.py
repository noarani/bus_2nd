import os
import glob

# ファイルパスを生の文字列リテラルで指定
files = glob.glob("D:\\いろいろ\\ダウンロード\\*シャトルバス時刻表*.pdf")

# 一致したファイルをすべて削除
for file in files:
    os.remove(file)
