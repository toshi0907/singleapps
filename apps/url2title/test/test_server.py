#!/usr/bin/env python3
"""url2title Web サーバーの API テスト"""

import http.client
import os
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
import server  # noqa: E402


class TestApiTitleEndpoint(unittest.TestCase):
    def setUp(self):
        self.httpd = server.HTTPServer(("127.0.0.1", 0), server.Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=1)

    def _request(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", path)
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        conn.close()
        return response.status, response.getheader("Content-Type"), body

    def test_api_title_success(self):
        with patch("server.fetch_title", return_value="Example Domain"):
            status, content_type, body = self._request(
                "/api/title?url=https%3A%2F%2Fexample.com"
            )

        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        self.assertIn('"ok": true', body)
        self.assertIn('"url": "https://example.com"', body)
        self.assertIn('"title": "Example Domain"', body)

    def test_api_title_missing_url(self):
        status, content_type, body = self._request("/api/title")

        self.assertEqual(status, 400)
        self.assertIn("application/json", content_type)
        self.assertIn('"ok": false', body)
        self.assertIn("url クエリパラメータを指定してください", body)

    def test_api_title_fetch_error(self):
        with patch("server.fetch_title", side_effect=RuntimeError("取得失敗")):
            status, content_type, body = self._request(
                "/api/title?url=https%3A%2F%2Fexample.com"
            )

        self.assertEqual(status, 500)
        self.assertIn("application/json", content_type)
        self.assertIn('"ok": false', body)
        self.assertIn("取得失敗", body)


if __name__ == "__main__":
    unittest.main()
