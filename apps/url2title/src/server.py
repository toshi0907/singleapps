#!/usr/bin/env python3
"""URLを入力するとそのページのタイトルを返す Web アプリ"""

import os
import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(__file__))
from url2title import fetch_title  # noqa: E402

DEFAULT_PORT = 8080

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>url2title</title>
</head>
<body>
  <h1>url2title</h1>
  <form method="get" action="/title">
    <label for="url">URL:</label>
    <input type="text" id="url" name="url" size="60" placeholder="https://example.com">
    <button type="submit">タイトルを取得</button>
  </form>
  {result}
</body>
</html>
"""


def _escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # デフォルトのアクセスログを抑制

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            self._serve_index()
        elif parsed.path == "/title":
            self._serve_title(parsed.query)
        elif parsed.path == "/api/title":
            self._serve_api_title(parsed.query)
        else:
            self._not_found()

    def _serve_index(self):
        body = HTML_TEMPLATE.format(result="").encode("utf-8")
        self._send_html(200, body)

    def _serve_title(self, query):
        params = urllib.parse.parse_qs(query)
        url = params.get("url", [""])[0].strip()
        if not url:
            result = "<p>URLを入力してください。</p>"
            body = HTML_TEMPLATE.format(result=result).encode("utf-8")
            self._send_html(400, body)
            return
        try:
            title = fetch_title(url)
            display = title if title else "(タイトルなし)"
            result = f"<p>タイトル: <strong>{_escape(display)}</strong></p>"
            body = HTML_TEMPLATE.format(result=result).encode("utf-8")
            self._send_html(200, body)
        except RuntimeError as e:
            result = f"<p>エラー: {_escape(str(e))}</p>"
            body = HTML_TEMPLATE.format(result=result).encode("utf-8")
            self._send_html(500, body)

    def _serve_api_title(self, query):
        params = urllib.parse.parse_qs(query)
        url = params.get("url", [""])[0].strip()
        if not url:
            self._send_json(
                400,
                {
                    "ok": False,
                    "error": "url クエリパラメータを指定してください",
                },
            )
            return

        try:
            title = fetch_title(url)
            self._send_json(
                200,
                {
                    "ok": True,
                    "url": url,
                    "title": title,
                },
            )
        except RuntimeError as e:
            self._send_json(
                500,
                {
                    "ok": False,
                    "error": str(e),
                },
            )

    def _not_found(self):
        body = b"Not Found"
        try:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # クライアント切断時はサーバー側で例外を握りつぶす。
            return

    def _send_html(self, status, body):
        try:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # クライアント切断時はサーバー側で例外を握りつぶす。
            return

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # クライアント切断時はサーバー側で例外を握りつぶす。
            return


def main():
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"エラー: ポート番号は整数で指定してください（例: 8080）", file=sys.stderr)
            sys.exit(1)
    server = HTTPServer(("", port), Handler)
    print(f"サーバーを起動しました: http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました")


if __name__ == "__main__":
    main()
