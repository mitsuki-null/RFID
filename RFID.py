import serial
import os
import pandas as pd
import keyboard
import time
import binascii

# RFIDからの受信データに対する一回の読み取りビットの設定
READ_BYTE = 32

# 在庫管理ファイルパスの指定
csv_file = "./warehouse_database.csv"

# 在庫管理データベースの初期化
df = pd.DataFrame()

# RFIDに読み取り命令を送る関数
def RFIDread(serial):
    # 送信するバイナリデータ（読み取り命令）
    binary_data = b'\x02\x00\x55\x07\x14\x02\x00\x00\x00\x00\x02\x03\x79\x0D'
    # データを送信
    serial.write(binary_data)

# 受信データの読み取り関数
# シリアルポートにバッファがあるため、readを読み込むたびにバッファから１行づつ呼び出される
def serialReadLine(serial):
    # データを受信
    received_data = serial.read(READ_BYTE)  # 最大[READ_BYTE]バイトまでのデータを受信
    hex_data = binascii.hexlify(received_data)
    print("Received Data:", hex_data.decode('utf-8'))
    return hex_data.decode('utf-8')

# 受信データの全てを読み取る関数
# シリアルポートにバッファがあるため、readを読み込むたびにバッファから１行づつ呼び出される => 読み取り文字がなくなるまでバッファから読み取る
def serialReadLines(serial):
    received_data_list = []
    while True:
        # データを受信
        received_data = serial.read(READ_BYTE)  # 最大[READ_BYTE]バイトまでのデータを受信
        hex_data = binascii.hexlify(received_data).decode("utf-8")

        if received_data and len(hex_data) == 64:  # 読み込んだデータがある　かつ　データ数が３２バイトの時（読み取り終了をリストに含まないため）
            received_data_list.append(hex_data[22:46]) # 商品IDのみを抽出して登録
            print("Received Data:", hex_data)
        
        else:  # 読み込んだデータがなければ
            print("LIST:")
            print(received_data_list)
            return received_data_list

# CSVファイルが存在するか確認
if os.path.exists(csv_file):
    # CSVファイルが存在する場合は読み込む
    df = pd.read_csv(csv_file)
    print("CSVファイルを読み込みました。")

else:
    # CSVファイルが存在しない場合は新しいデータを作成
    data = {
        'ID': [],
        'exsistence': []
    }
    df = pd.DataFrame(data)
    
    # 新しいデータをCSVファイルとして保存
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)  # ディレクトリが存在しない場合は作成
    df.to_csv(csv_file, index=False)
    print("新しいCSVファイルを作成しました。")

# 以下RFID読み取り関連
# シリアルポートを開く
ser = serial.Serial(
    port='COM3',  # 使用しているポート名に変更 (WindowsではCOMポート、Linux/macOSでは/dev/ttyUSBxなど)
    baudrate=115200,  # ボーレート
    timeout=1  # タイムアウト（必要に応じて調整）
)

while True:

    print("READ")

    # RFIDへのREAD命令
    RFIDread(ser)

    # 受信データの読み取り
    rcv_data_list = serialReadLines(ser)

    # 全てのデータの取り出し
    for rcv_data in rcv_data_list:

    # 読み取ったデータのIDがすでに存在するか
        check_str = df[df["ID"].isin([rcv_data])]
        # print("CHECK_STR")
        # print(check_str)
        # print(check_str[1])


        # rcv_dataで得たIDがデータベースに存在しない場合
        if(check_str.empty):
            # IDをデータベースに登録
            new_data = pd.DataFrame({"ID": [rcv_data], "exsistence": [True]})
            df = pd.concat([df, new_data], ignore_index=True)
            print("ID: " + rcv_data +"をデータベースに登録しました。")

        # rcv_dataで得たIDがデータベースに存在する場合
        # 中でも倉庫内に保管されている場合
        elif(check_str.iloc[0]["exsistence"] == True):
            # 指定IDの保管データをFalseに（貸し出し処理）
            df.loc[df["ID"] == rcv_data, "exsistence"] = False
            print("ID: " + rcv_data +"を貸し出しました。")
        
        # 倉庫内に保管されていない場合
        elif(check_str.iloc[0]["exsistence"] == False):
            #指定IDの保管データをTrueに（返却処理）
            df.loc[df["ID"] == rcv_data, "exsistence"] = True
            print("ID: " + rcv_data +"を返却しました。")
        
        else:
            print("データベース記録エラー")
        
    # CSVファイルを更新
    df.to_csv(csv_file, index=False)

    
    # ESCキーが押されたかチェック
    if keyboard.is_pressed('esc'):
        print("ESC キーが押されました。プログラムを終了します。")
        break  # ループを終了

    # 1秒待機（お好みで調整してください）
    time.sleep(1)

# ポートを閉じる
ser.close()
