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
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".webm"}

HTML = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>音声再生プレイヤー</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #333; }
    h1 { margin-bottom: 24px; font-size: 1.6rem; }
    h2 { font-size: 1.1rem; margin-bottom: 12px; }
    .card {
      margin-bottom: 24px;
      padding: 20px;
      border: 1px solid #ddd;
      border-radius: 8px;
      background: #fafafa;
    }
    #file-list { list-style: none; }
    #file-list li {
      padding: 8px 12px;
      cursor: pointer;
      border-radius: 4px;
      transition: background 0.15s;
      word-break: break-all;
    }
    #file-list li:hover { background: #e8e8e8; }
    #file-list li.active { background: #dbeafe; font-weight: bold; }
    #no-files { color: #888; }
    #current-file { margin-bottom: 12px; color: #555; font-style: italic; min-height: 1.2em; }
    #controls { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
    #controls button {
      padding: 8px 18px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.95rem;
      transition: opacity 0.15s;
    }
    #controls button:disabled { opacity: 0.4; cursor: not-allowed; }
    #play-btn { background: #22c55e; color: #fff; }
    #stop-btn { background: #ef4444; color: #fff; }
    .volume-wrap { display: flex; align-items: center; gap: 8px; }
    #volume { width: 100px; cursor: pointer; }
    #progress-wrap { margin-bottom: 4px; }
    #progress { width: 100%; height: 6px; cursor: pointer; accent-color: #3b82f6; }
    #time-display { font-size: 0.82rem; color: #666; }
    #upload-form { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
    #upload-form button {
      padding: 8px 16px;
      background: #3b82f6;
      color: #fff;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    #upload-form button:disabled { opacity: 0.4; cursor: not-allowed; }
    #upload-msg { margin-top: 8px; font-size: 0.9rem; }
    .ok { color: #16a34a; }
    .err { color: #dc2626; }
  </style>
</head>
<body>
  <h1>🎵 音声再生プレイヤー</h1>

  <div class="card">
    <h2>ファイル一覧</h2>
    <ul id="file-list"><li id="no-files">ファイルがありません</li></ul>
  </div>

  <div class="card">
    <p id="current-file">ファイルを選択してください</p>
    <audio id="audio" preload="auto"></audio>
    <div id="progress-wrap">
      <input type="range" id="progress" min="0" max="1" step="0.001" value="0">
    </div>
    <p id="time-display">0:00 / 0:00</p>
    <div id="controls">
      <button id="play-btn" disabled>▶ 再生</button>
      <button id="stop-btn" disabled>■ 停止</button>
      <div class="volume-wrap">
        <label for="volume">🔊</label>
        <input type="range" id="volume" min="0" max="1" step="0.01" value="1">
        <span id="volume-val">100%</span>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>ファイルをアップロード</h2>
    <form id="upload-form" enctype="multipart/form-data">
      <input type="file" id="file-input" accept="audio/*,.mp3,.wav,.ogg,.flac,.aac,.m4a,.webm">
      <button type="submit" id="upload-btn">アップロード</button>
    </form>
    <p id="upload-msg"></p>
  </div>

  <script>
    const audio = document.getElementById('audio');
    const playBtn = document.getElementById('play-btn');
    const stopBtn = document.getElementById('stop-btn');
    const volumeSlider = document.getElementById('volume');
    const volumeVal = document.getElementById('volume-val');
    const progress = document.getElementById('progress');
    const timeDisplay = document.getElementById('time-display');
    const currentFileLabel = document.getElementById('current-file');
    const fileList = document.getElementById('file-list');

    fetchFiles();

    function fetchFiles() {
      fetch('/api/files')
        .then(r => r.json())
        .then(data => {
          fileList.innerHTML = '';
          if (!data.files || data.files.length === 0) {
            fileList.innerHTML = '<li id="no-files">ファイルがありません</li>';
            return;
          }
          data.files.forEach(f => {
            const li = document.createElement('li');
            li.textContent = f;
            li.onclick = () => loadFile(f, li);
            fileList.appendChild(li);
          });
        })
        .catch(() => {
          fileList.innerHTML = '<li id="no-files">一覧の取得に失敗しました</li>';
        });
    }

    function loadFile(filename, li) {
      document.querySelectorAll('#file-list li').forEach(el => el.classList.remove('active'));
      li.classList.add('active');
      currentFileLabel.textContent = filename;
      audio.src = '/audio/' + encodeURIComponent(filename);
      audio.load();
      playBtn.disabled = false;
      stopBtn.disabled = false;
      audio.play().then(() => {
        playBtn.textContent = '⏸ 一時停止';
      }).catch(() => {});
    }

    playBtn.addEventListener('click', () => {
      if (audio.paused) {
        audio.play().then(() => {
          playBtn.textContent = '⏸ 一時停止';
        }).catch(() => {});
      } else {
        audio.pause();
        playBtn.textContent = '▶ 再生';
      }
    });

    stopBtn.addEventListener('click', () => {
      audio.pause();
      audio.currentTime = 0;
      playBtn.textContent = '▶ 再生';
    });

    audio.addEventListener('ended', () => {
      playBtn.textContent = '▶ 再生';
    });

    audio.addEventListener('timeupdate', () => {
      if (audio.duration && isFinite(audio.duration)) {
        progress.value = audio.currentTime / audio.duration;
        timeDisplay.textContent = fmt(audio.currentTime) + ' / ' + fmt(audio.duration);
      }
    });

    progress.addEventListener('input', () => {
      if (audio.duration && isFinite(audio.duration)) {
        audio.currentTime = progress.value * audio.duration;
      }
    });

    volumeSlider.addEventListener('input', () => {
      audio.volume = volumeSlider.value;
      volumeVal.textContent = Math.round(volumeSlider.value * 100) + '%';
    });

    function fmt(sec) {
      const m = Math.floor(sec / 60);
      const s = Math.floor(sec % 60);
      return m + ':' + String(s).padStart(2, '0');
    }

    document.getElementById('upload-form').addEventListener('submit', e => {
      e.preventDefault();
      const file = document.getElementById('file-input').files[0];
      const msg = document.getElementById('upload-msg');
      const btn = document.getElementById('upload-btn');
      if (!file) {
        msg.textContent = 'ファイルを選択してください';
        msg.className = 'err';
        return;
      }
      btn.disabled = true;
      msg.textContent = 'アップロード中...';
      msg.className = '';
      const fd = new FormData();
      fd.append('file', file);
      fetch('/upload', { method: 'POST', body: fd })
        .then(r => r.json())
        .then(data => {
          if (data.ok) {
            msg.textContent = 'アップロード完了: ' + data.filename;
            msg.className = 'ok';
            fetchFiles();
          } else {
            msg.textContent = 'エラー: ' + data.error;
            msg.className = 'err';
          }
        })
        .catch(() => {
          msg.textContent = 'アップロードに失敗しました';
          msg.className = 'err';
        })
        .finally(() => { btn.disabled = false; });
    });
  </script>
</body>
</html>
"""


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
        body = HTML.encode("utf-8")
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
