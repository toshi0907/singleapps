#!/usr/bin/env python3
"""アナログ・デジタル時計を表示する Web アプリ"""

import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

DEFAULT_PORT = 8080
SRC_DIR = os.path.dirname(os.path.abspath(__file__))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002
        print(f"[{self.log_date_time_string()}] {format % args}")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._serve_file("index.html", "text/html; charset=utf-8")
        else:
            self._not_found()

    def _serve_file(self, filename, content_type):
        filepath = os.path.join(SRC_DIR, filename)
        try:
            with open(filepath, "rb") as f:
                body = f.read()
        except OSError:
            self._not_found()
            return
        try:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _not_found(self):
        body = b"Not Found"
        try:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
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
