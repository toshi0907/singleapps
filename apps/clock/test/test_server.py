#!/usr/bin/env python3
"""clock サーバーのテスト"""

import io
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
from server import Handler, DEFAULT_PORT  # noqa: E402


class MockRequest:
    """BaseHTTPRequestHandler に渡す最小限のソケットモック"""

    def __init__(self):
        self._data = b""

    def makefile(self, mode, *args, **kwargs):
        if "r" in mode:
            return io.BytesIO(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        return io.BytesIO()

    def sendall(self, data):
        self._data += data


def _make_handler(method="GET", path="/"):
    """Handler を直接インスタンス化するためのファクトリ"""
    request = MockRequest()
    client_address = ("127.0.0.1", 9999)

    # server モックには socket が必要
    server_mock = MagicMock()
    server_mock.socket = MagicMock()

    handler = Handler.__new__(Handler)
    handler.request       = request
    handler.client_address = client_address
    handler.server        = server_mock
    handler.command       = method
    handler.path          = path
    handler.headers       = {}
    handler.wfile         = io.BytesIO()
    handler.rfile         = io.BytesIO()
    handler.requestline   = f"{method} {path} HTTP/1.1"
    return handler


class TestHandlerRouting(unittest.TestCase):
    def test_root_returns_200(self):
        handler = _make_handler("GET", "/")
        with patch.object(handler, "send_response") as mock_resp, \
             patch.object(handler, "send_header"), \
             patch.object(handler, "end_headers"):
            handler.do_GET()
            mock_resp.assert_called_once_with(200)

    def test_index_html_returns_200(self):
        handler = _make_handler("GET", "/index.html")
        with patch.object(handler, "send_response") as mock_resp, \
             patch.object(handler, "send_header"), \
             patch.object(handler, "end_headers"):
            handler.do_GET()
            mock_resp.assert_called_once_with(200)

    def test_unknown_path_returns_404(self):
        handler = _make_handler("GET", "/notfound")
        with patch.object(handler, "send_response") as mock_resp, \
             patch.object(handler, "send_header"), \
             patch.object(handler, "end_headers"):
            handler.do_GET()
            mock_resp.assert_called_once_with(404)

    def test_response_body_contains_clock_html(self):
        handler = _make_handler("GET", "/")
        with patch.object(handler, "send_response"), \
             patch.object(handler, "send_header"), \
             patch.object(handler, "end_headers"):
            handler.do_GET()
        handler.wfile.seek(0)
        body = handler.wfile.read()
        self.assertIn(b"<canvas", body)
        self.assertIn(b"analog", body)


class TestDefaultPort(unittest.TestCase):
    def test_default_port(self):
        self.assertEqual(DEFAULT_PORT, 8080)


if __name__ == "__main__":
    unittest.main()
