#!/usr/bin/env python3
"""URLを入力するとそのページのタイトルを返す CLI ツール"""

import html.parser
import sys
import urllib.parse
import urllib.request


class TitleParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self._in_title = False
        self.title = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and self.title is None:
            self.title = data.strip()


def fetch_title(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise RuntimeError("URLは http:// または https:// で始まる必要があります")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "url2title/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            html_text = content.decode(charset, errors="replace")
    except Exception as e:
        raise RuntimeError(f"URLの取得に失敗しました: {e}") from e

    parser = TitleParser()
    parser.feed(html_text)
    return parser.title


def main():
    if len(sys.argv) != 2:
        print(f"使い方: {sys.argv[0]} <URL>", file=sys.stderr)
        print("例: python url2title.py https://example.com", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    try:
        title = fetch_title(url)
        if title:
            print(title)
        else:
            print("(タイトルなし)")
    except RuntimeError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
