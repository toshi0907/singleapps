#!/usr/bin/env python3
"""音声再生 Web サーバーのテスト"""

import http.client
import io
import json
import os
import pathlib
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
import server  # noqa: E402


class TestAudioPlayerServer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        tmp = pathlib.Path(self.tmpdir.name)
        self._orig_sounds = server.SOUNDS_DIR
        self._orig_uploads = server.UPLOADS_DIR
        server.SOUNDS_DIR = tmp / "sounds"
        server.UPLOADS_DIR = tmp / "uploads"
        server.SOUNDS_DIR.mkdir()
        server.UPLOADS_DIR.mkdir()

        self.httpd = server.HTTPServer(("127.0.0.1", 0), server.Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=1)
        server.SOUNDS_DIR = self._orig_sounds
        server.UPLOADS_DIR = self._orig_uploads
        self.tmpdir.cleanup()

    def _get(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", path)
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp.status, resp.getheader("Content-Type"), body

    # --- GET / ---

    def test_index_returns_200_html(self):
        status, content_type, body = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(b"\xe9\x9f\xb3\xe5\xa3\xb0\xe5\x86\x8d\xe7\x94\x9f", body)  # "音声再生" in UTF-8

    # --- GET /api/files ---

    def test_api_files_empty(self):
        status, content_type, body = self._get("/api/files")
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        data = json.loads(body)
        self.assertEqual(data["files"], [])

    def test_api_files_lists_sounds_dir(self):
        (server.SOUNDS_DIR / "sample.mp3").write_bytes(b"")
        status, _, body = self._get("/api/files")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertIn("sample.mp3", data["files"])

    def test_api_files_lists_uploads_dir(self):
        (server.UPLOADS_DIR / "uploaded.wav").write_bytes(b"")
        status, _, body = self._get("/api/files")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertIn("uploaded.wav", data["files"])

    def test_api_files_ignores_non_audio(self):
        (server.SOUNDS_DIR / "notes.txt").write_bytes(b"")
        status, _, body = self._get("/api/files")
        data = json.loads(body)
        self.assertNotIn("notes.txt", data["files"])

    # --- GET /audio/<filename> ---

    def test_audio_serves_file(self):
        content = b"FAKE_AUDIO_DATA"
        (server.SOUNDS_DIR / "test.mp3").write_bytes(content)
        status, content_type, body = self._get("/audio/test.mp3")
        self.assertEqual(status, 200)
        self.assertEqual(body, content)

    def test_audio_not_found(self):
        status, _, _ = self._get("/audio/nonexistent.mp3")
        self.assertEqual(status, 404)

    def test_audio_directory_traversal_blocked(self):
        # /../ を含むパスはファイルが見つからず 404 になること
        status, _, _ = self._get("/audio/../server.py")
        self.assertEqual(status, 404)

    def test_audio_range_request(self):
        content = b"0123456789"
        (server.SOUNDS_DIR / "range.mp3").write_bytes(content)
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", "/audio/range.mp3", headers={"Range": "bytes=2-5"})
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        self.assertEqual(resp.status, 206)
        self.assertEqual(body, b"2345")

    # --- POST /upload ---

    def test_upload_valid_file(self):
        boundary = b"----TestBoundary"
        file_content = b"FAKE_WAV"
        body = (
            b"--" + boundary + b"\r\n"
            b'Content-Disposition: form-data; name="file"; filename="upload.wav"\r\n'
            b"Content-Type: audio/wav\r\n\r\n"
            + file_content
            + b"\r\n--" + boundary + b"--\r\n"
        )
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(
            "POST",
            "/upload",
            body=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary=----TestBoundary",
                "Content-Length": str(len(body)),
            },
        )
        resp = conn.getresponse()
        data = json.loads(resp.read())
        conn.close()
        self.assertEqual(resp.status, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["filename"], "upload.wav")
        self.assertTrue((server.UPLOADS_DIR / "upload.wav").exists())

    def test_upload_invalid_extension(self):
        boundary = b"----TestBoundary2"
        body = (
            b"--" + boundary + b"\r\n"
            b'Content-Disposition: form-data; name="file"; filename="script.exe"\r\n'
            b"Content-Type: application/octet-stream\r\n\r\n"
            b"data"
            b"\r\n--" + boundary + b"--\r\n"
        )
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(
            "POST",
            "/upload",
            body=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary=----TestBoundary2",
                "Content-Length": str(len(body)),
            },
        )
        resp = conn.getresponse()
        data = json.loads(resp.read())
        conn.close()
        self.assertEqual(resp.status, 400)
        self.assertFalse(data["ok"])

    # --- 404 ---

    def test_unknown_path_returns_404(self):
        status, _, _ = self._get("/no/such/path")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
