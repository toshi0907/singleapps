#!/usr/bin/env python3
"""音声ファイルを再生する Web アプリ"""

import cgi
import json
import mimetypes
import os
import pathlib
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

DEFAULT_PORT = 8080
SCRIPT_DIR = pathlib.Path(__file__).parent
SOUNDS_DIR = SCRIPT_DIR.parent / "sounds"
UPLOADS_DIR = SCRIPT_DIR.parent / "uploads"
INDEX_HTML = SCRIPT_DIR / "index.html"
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".webm"}


def _list_audio_files():
    """sounds/ と uploads/ 内の音声ファイルを一覧で返す。"""
    files = []
    for directory in [SOUNDS_DIR, UPLOADS_DIR]:
        if directory.exists():
            for f in sorted(directory.iterdir()):
                if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS:
                    files.append(f.name)
    return files


def _find_audio_file(filename):
    """sounds/ または uploads/ からファイルを探す。見つからなければ None を返す。"""
    safe = pathlib.Path(filename).name  # ディレクトリトラバーサル防止
    for directory in [SOUNDS_DIR, UPLOADS_DIR]:
        candidate = directory / safe
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # デフォルトのアクセスログを抑制

    def do_GET(self):
        if self.path == "/":
            self._serve_index()
        elif self.path == "/api/files":
            self._serve_file_list()
        elif self.path.startswith("/audio/"):
            filename = self.path[len("/audio/"):]
            import urllib.parse
            filename = urllib.parse.unquote(filename)
            self._serve_audio(filename)
        else:
            self._not_found()

    def do_POST(self):
        if self.path == "/upload":
            self._handle_upload()
        else:
            self._not_found()

    def _serve_index(self):
        body = INDEX_HTML.read_bytes()
        self._send_response(200, "text/html; charset=utf-8", body)

    def _serve_file_list(self):
        files = _list_audio_files()
        self._send_json(200, {"files": files})

    def _serve_audio(self, filename):
        file_path = _find_audio_file(filename)
        if file_path is None:
            self._not_found()
            return
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "application/octet-stream"
        file_size = file_path.stat().st_size
        range_header = self.headers.get("Range")
        if range_header:
            m = re.match(r"bytes=(\d*)-(\d*)", range_header)
            if m:
                start = int(m.group(1)) if m.group(1) else 0
                end = int(m.group(2)) if m.group(2) else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1
                try:
                    self.send_response(206)
                    self.send_header("Content-Type", mime_type)
                    self.send_header("Content-Length", str(length))
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Accept-Ranges", "bytes")
                    self.end_headers()
                    with open(file_path, "rb") as f:
                        f.seek(start)
                        self.wfile.write(f.read(length))
                except (BrokenPipeError, ConnectionResetError):
                    return
                return
        try:
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        except (BrokenPipeError, ConnectionResetError):
            return

    def _handle_upload(self):
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))
        if not content_type.startswith("multipart/form-data"):
            self._send_json(400, {"ok": False, "error": "multipart/form-data で送信してください"})
            return
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": str(content_length),
        }
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ=environ)
        if "file" not in form:
            self._send_json(400, {"ok": False, "error": "ファイルが指定されていません"})
            return
        file_item = form["file"]
        if not file_item.filename:
            self._send_json(400, {"ok": False, "error": "ファイルが指定されていません"})
            return
        filename = pathlib.Path(file_item.filename).name
        ext = pathlib.Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            self._send_json(
                400,
                {
                    "ok": False,
                    "error": f"対応していない形式です: {ext}。対応形式: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
                },
            )
            return
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        save_path = UPLOADS_DIR / filename
        with open(save_path, "wb") as f:
            f.write(file_item.file.read())
        self._send_json(200, {"ok": True, "filename": filename})

    def _not_found(self):
        try:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Not Found")
        except (BrokenPipeError, ConnectionResetError):
            return

    def _send_response(self, status, content_type, body):
        try:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_response(status, "application/json; charset=utf-8", body)


def main():
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("エラー: ポート番号は整数で指定してください（例: 8080）", file=sys.stderr)
            sys.exit(1)
    server = HTTPServer(("", port), Handler)
    print(f"サーバーを起動しました: http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました")


if __name__ == "__main__":
    main()
