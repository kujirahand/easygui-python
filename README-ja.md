# TkEasyGUI

`TkEasyGUI`は、**Pythonで最も簡単にGUIアプリケーション開発するライブラリ**です。`Tkinter`のような従来のUIライブラリが持つ複雑さを解消し、より多くの開発者がGUIアプリの開発を楽しめます。本ライブラリは、簡単にGUIを構築できるライブラリ`PySimpleGUI`の概念を引き継ぎつつ、独自の機能を追加しています。

- [👉English](https://github.com/kujirahand/tkeasygui-python/blob/main/README.md)

## TkEasyGUIの特徴:

- `TkEasyGUI`は、GUIアプリケーションを簡単かつシンプルに作成することができるPythonライブラリです。
- イベントモデルでは、よく知られたGUIライブラリ`PySimpleGUI`と互換性があります。
- Pythonの標準UIライブラリ`Tkinter`は、学習障壁が高と考えられていますが、このライブラリを使用すると、GUIアプリケーションを直感的に作成できます。
- 型ヒントに対応しているので、コード補完でプロパティを選択できます。(本パッケージの利用には、`Python 3.9以降`が必要です。)
- ライセンスには比較的緩い`MITライセンス`を採用しています。将来このライセンスを変えることはありません。

## 対象プラットフォーム

- Windows / macOS / Linux (Tkinterが動く環境)

## インストール:

pypiからインストールします。

```sh
python -m pip install TkEasyGUI
```

GitHubリポジトリからインストールします。

```sh
python -m pip install git+https://github.com/kujirahand/tkeasygui-python
```

- (memo) v0.2.24未満のバージョンからのアップデートに失敗する場合があります。その場合、[こちら](docs/installation_trouble.md)を確認してください。

## 簡単な使い方 - ポップアップダイアログを使う

TkEasyGUIの使い方は簡単です。もし、ダイアログにメッセージを表示したい場合、次のように記述します。

```py
import TkEasyGUI as eg
eg.print("A joyful heart is good medicine.")
```

入力ボックス付きのダイアログで尋ねることもできます。次のコードは、名前を尋ねて、続くダイアログに名前を表示します。

```py
import TkEasyGUI as eg
name = eg.input("What is your name?")
eg.print(f"Hello, {name}.")
```

## 簡単な使い方 - カスタムウィンドウを定義して使う

ラベルとボタンのみを持つシンプルなウィンドウを作成するには、以下のように記述します。`with`文を使うことで、イベントループを抜けると自動的にウィンドウが閉じるように指定できます。

```py
import TkEasyGUI as eg
# 画面レイアウトの定義
layout = [
    [eg.Text("Hello, World!")],
    [eg.Button("OK")]
]
# ウィンドウを表示する
with eg.Window("Hello App", layout) as window:
    # イベントループを処理する
    for event, values in window.event_iter():
        if event == "OK":
            eg.print("Thank you.")
            break # ループを抜ける
```

有名GUIライブラリの`PySimpleGUI`と同じイベントモデルの使い勝手で記述できます。（多くのGUI部品でPySimpleGUIと互換性を持たせています。）

```py
import TkEasyGUI as eg
# define layout
layout = [[eg.Text("Hello, World!")],
          [eg.Button("Exit")]]
# create a window
window = eg.Window("test", layout)
# event loop
while True:
    event, values = window.read()
    if event in ["Exit", eg.WINDOW_CLOSED]:
        eg.popup("Thank you.")
        break
# close window
window.close()
```

- [Docs > どんなElementが使えますか？](https://github.com/kujirahand/tkeasygui-python/blob/main/docs/README.md#tkeasygui-elements-list)

## チュートリアル

- [(note) TkEasyGUI - Pythonで最も素早くデスクトップアプリを創るライブラリ](https://note.com/kujirahand/n/n33a2df3aa3e5)
- [(マイナビPython連載) (116回目)金額合計ツールでExcel要らず - 合計/整形/コピーのツールを作ろう](https://news.mynavi.jp/techplus/article/zeropython-116/)
- [(書籍) Pythonでつくるデスクトップアプリ メモ帳からスクレイピング・生成AI利用まで](https://amzn.to/45R2NSH)

## サンプル

簡単な使い方を示すサンプルを揃えました。確認してみてください。

- [samples](https://github.com/kujirahand/tkeasygui-python/tree/main/tests).

`tests/file_viewer.py`を実行することで、すべてのサンプルを手軽に起動できます。

## ドキュメント

ライブラリの詳細なクラスやメソッドの一覧です。

- [docs](https://github.com/kujirahand/tkeasygui-python/tree/main/docs)

## PySimpleGUIとの関係について

- 基本機能を使う場合、PySimpleGUIと互換性があります。PySimpleGUIと同じイベントモデルでプログラムを記述できます。
- 基本的なGUI部品の名前も同じにしてあります。しかし、いくつかのプロパティの名前が異なっていますが、多くの独自機能が実装されています。
- 本プロジェクトは、PySimpleGUIの存在を意識して開発しましたが、完全にゼロから実装しています。ライセンス的にも問題はありません。

PySimpleGUIと完全な互換性は考えていません。

### TkEasyGUI独自の機能

- for文と `window.event_iter()` を使って気軽にイベント処理が可能
- 任意のボタンを持つダイアログ(eg.popup_buttons)や色選択ダイアログ(eg.popup_color)など、独自のポップアップダイアログを用意
- ImageはPNGだけでなくJPEGも読み込み可能
- 便利なイベントフックや一括イベント登録機能 - [docs/custom_events](docs/custom_events.md)
- テキストボックス(Muliline/Input)に便利なCopy/Paste/Cutなどのメソッドを追加

## リンク

- [pypi.org > TkEasyGUI](https://pypi.org/project/tkeasygui/)
- [GitHub > TkEasyGUI](https://github.com/kujirahand/tkeasygui-python/)
- [Discord > TkEasyGUI](https://discord.gg/G2JXaRft)

