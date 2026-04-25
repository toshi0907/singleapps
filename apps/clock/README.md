# clock

アナログ時計とデジタル時計を同時に表示する Web アプリです。  
1 秒ごとに自動更新し、タイムゾーンをドロップダウンで切り替えられます。

## 前提環境

- Python 3.8 以上
- モダンブラウザ（HTML5 Canvas / `Intl.DateTimeFormat` 対応）

## 使い方

```sh
python src/server.py [ポート番号]
```

ポート番号を省略した場合は `8080` で起動します。

起動後、ブラウザで `http://localhost:8080` にアクセスすると時計が表示されます。

### 起動例

```sh
$ python src/server.py
サーバーを起動しました: http://localhost:8080
```

カスタムポートで起動する場合:

```sh
$ python src/server.py 9000
サーバーを起動しました: http://localhost:9000
```

## 機能

| 機能 | 説明 |
|------|------|
| アナログ時計 | Canvas で描画。時・分・秒針を表示 |
| デジタル時計 | `HH:MM:SS` 形式で表示。日付・曜日も併記 |
| 1 秒更新 | `setInterval` で毎秒自動更新 |
| タイムゾーン変更 | ドロップダウンで切り替え（デフォルト: 日本 JST） |

### 対応タイムゾーン

日本（Asia/Tokyo）をデフォルトとし、以下を選択できます。

- UTC
- ロンドン (GMT/BST)
- パリ (CET/CEST)
- ニューヨーク (EST/EDT)
- シカゴ (CST/CDT)
- ロサンゼルス (PST/PDT)
- 上海 (CST, UTC+8)
- 香港 (HKT, UTC+8)
- シンガポール (SGT, UTC+8)
- ドバイ (GST, UTC+4)
- シドニー (AEST/AEDT)
- オークランド (NZST/NZDT)

## テスト

```sh
python -m unittest discover -s test -v
```

## 想定ユースケースと制約

- ローカル環境でブラウザに時計を表示したい場合に使用します。
- 外部依存はなく、Python 標準ライブラリのみで動作します。
- タイムゾーンの表示は `Intl.DateTimeFormat`（ブラウザ標準 API）を使用します。
