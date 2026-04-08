# url2title

URL を入力するとそのページのタイトルを返すアプリです。CLI と Web の 2 種類を提供します。

## 前提環境

- Python 3.6 以上
- 外部依存なし（標準ライブラリのみ使用）

## 使い方

### CLI アプリ

```sh
python src/url2title.py <URL>
```

#### 入出力例

```sh
$ python src/url2title.py https://example.com
Example Domain
```

引数なしで実行すると使い方を表示します。

```sh
$ python src/url2title.py
使い方: src/url2title.py <URL>
例: python url2title.py https://example.com
```

### Web アプリ

```sh
python src/server.py [ポート番号]
```

ポート番号を省略した場合は `8080` で起動します。

起動後、ブラウザで `http://localhost:8080` にアクセスし、フォームに URL を入力してタイトルを取得できます。

JSON API を使う場合は、`/api/title` に `url` クエリパラメータを指定してアクセスします。

```sh
curl --get 'http://localhost:8080/api/title' --data-urlencode 'url=https://example.com'
```

レスポンス例:

```json
{"ok": true, "url": "https://example.com", "title": "Example Domain"}
```

#### 起動例

```sh
$ python src/server.py
サーバーを起動しました: http://localhost:8080
```

カスタムポートで起動する場合:

```sh
$ python src/server.py 9000
サーバーを起動しました: http://localhost:9000
```

## テスト

```sh
python3 test/test_url2title.py
```

## 想定ユースケースと制約

- **ユースケース**: 複数の URL のタイトルをまとめて確認したい場合、またはブラウザを開かずに URL の内容を素早く確認したい場合に便利です。
- **制約**:
  - JavaScript によって動的に設定されるタイトルは取得できません（静的な HTML の `<title>` タグのみ対象）。
  - アクセス制限があるページ（認証が必要なページなど）は取得できない場合があります。
  - タイムアウトは 10 秒です。
