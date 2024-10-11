from flask import Flask, render_template, send_from_directory
import pandas as pd
import os
import time
import threading

app = Flask(__name__, template_folder="./")

# CSVファイルを読み込み
csv_file = "./warehouse_database.csv"
df = pd.read_csv(csv_file)

# CSVファイルの読み込みを行う関数
def load_csv():
    global df
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        print("CSVファイルを読み込みました。")
    else:
        print("CSVファイルが見つかりません。")

# CSVファイルの読み込みを定期的に行う関数
def load_csv_periodically():
    while True:
        load_csv()  # CSVを読み込む
        time.sleep(4)  # 4秒ごとに読み込み

# Flaskアプリを起動する前にスレッドを開始
threading.Thread(target=load_csv_periodically, daemon=True).start()

@app.route('/')
def index():
    # テーブルをHTMLに変換
    table = df.to_html(classes='table table-striped', index=False)
    return render_template('index.html', table=table)

# 静的ファイルを提供するためのルート
@app.route('/<path:path>')
def send_css(path):
    return send_from_directory('.', path)


if __name__ == '__main__':
    app.run(debug=True)
