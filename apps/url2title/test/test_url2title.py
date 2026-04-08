#!/usr/bin/env python3
"""url2title のテスト"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
from url2title import TitleParser, fetch_title  # noqa: E402


class TestTitleParser(unittest.TestCase):
    def test_simple_title(self):
        parser = TitleParser()
        parser.feed("<html><head><title>Hello World</title></head></html>")
        self.assertEqual(parser.title, "Hello World")

    def test_no_title(self):
        parser = TitleParser()
        parser.feed("<html><head></head></html>")
        self.assertIsNone(parser.title)

    def test_title_with_whitespace(self):
        parser = TitleParser()
        parser.feed("<html><head><title>  Trimmed  </title></head></html>")
        self.assertEqual(parser.title, "Trimmed")

    def test_japanese_title(self):
        parser = TitleParser()
        parser.feed("<html><head><title>日本語タイトル</title></head></html>")
        self.assertEqual(parser.title, "日本語タイトル")

    def test_only_first_title_used(self):
        parser = TitleParser()
        parser.feed("<title>First</title><title>Second</title>")
        self.assertEqual(parser.title, "First")


class TestFetchTitle(unittest.TestCase):
    def _make_mock_response(self, html_bytes, charset="utf-8"):
        mock_response = MagicMock()
        mock_response.read.return_value = html_bytes
        mock_response.headers.get_content_charset.return_value = charset
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    def test_fetch_title_success(self):
        mock_response = self._make_mock_response(
            b"<html><head><title>Test Page</title></head></html>"
        )
        with patch("urllib.request.urlopen", return_value=mock_response):
            title = fetch_title("https://example.com")
        self.assertEqual(title, "Test Page")

    def test_fetch_title_no_title_tag(self):
        mock_response = self._make_mock_response(
            b"<html><head></head><body>no title</body></html>"
        )
        with patch("urllib.request.urlopen", return_value=mock_response):
            title = fetch_title("https://example.com")
        self.assertIsNone(title)

    def test_fetch_title_network_failure(self):
        with patch("urllib.request.urlopen", side_effect=Exception("接続失敗")):
            with self.assertRaises(RuntimeError):
                fetch_title("https://example.com")

    def test_fetch_title_fallback_charset(self):
        mock_response = self._make_mock_response(
            b"<html><head><title>Fallback</title></head></html>",
            charset=None,
        )
        with patch("urllib.request.urlopen", return_value=mock_response):
            title = fetch_title("https://example.com")
        self.assertEqual(title, "Fallback")

    def test_fetch_title_invalid_scheme(self):
        with self.assertRaises(RuntimeError):
            fetch_title("file:///etc/passwd")


if __name__ == "__main__":
    unittest.main()
