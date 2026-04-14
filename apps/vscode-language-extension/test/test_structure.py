#!/usr/bin/env python3
"""vscode-language-extension テンプレートの JSON 構造を検証するテスト"""

import json
import os
import sys

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_package_json():
    pkg = load_json(os.path.join(BASE_DIR, "package.json"))

    assert "name" in pkg, "package.json に 'name' フィールドがありません"
    assert "version" in pkg, "package.json に 'version' フィールドがありません"
    assert "engines" in pkg, "package.json に 'engines' フィールドがありません"
    assert "vscode" in pkg["engines"], "engines に 'vscode' フィールドがありません"

    contributes = pkg.get("contributes", {})
    assert "languages" in contributes, "contributes に 'languages' がありません"
    assert "grammars" in contributes, "contributes に 'grammars' がありません"

    lang = contributes["languages"][0]
    assert "id" in lang, "languages[0] に 'id' がありません"
    assert "extensions" in lang, "languages[0] に 'extensions' がありません"
    assert "configuration" in lang, "languages[0] に 'configuration' がありません"

    grammar = contributes["grammars"][0]
    assert "language" in grammar, "grammars[0] に 'language' がありません"
    assert "scopeName" in grammar, "grammars[0] に 'scopeName' がありません"
    assert "path" in grammar, "grammars[0] に 'path' がありません"

    print("ok: package.json")


def test_language_configuration_json():
    cfg = load_json(os.path.join(BASE_DIR, "language-configuration.json"))

    assert "comments" in cfg, "language-configuration.json に 'comments' がありません"
    assert "lineComment" in cfg["comments"], "comments に 'lineComment' がありません"
    assert "brackets" in cfg, "language-configuration.json に 'brackets' がありません"
    assert "autoClosingPairs" in cfg, "language-configuration.json に 'autoClosingPairs' がありません"

    print("ok: language-configuration.json")


def test_grammar_json():
    grammar = load_json(
        os.path.join(BASE_DIR, "syntaxes", "mylang.tmLanguage.json")
    )

    assert "scopeName" in grammar, "tmLanguage.json に 'scopeName' がありません"
    assert "patterns" in grammar, "tmLanguage.json に 'patterns' がありません"
    assert "repository" in grammar, "tmLanguage.json に 'repository' がありません"

    repo = grammar["repository"]
    for key in ("comments", "keywords", "strings", "numbers"):
        assert key in repo, f"repository に '{key}' がありません"

    print("ok: syntaxes/mylang.tmLanguage.json")


def test_grammar_path_consistency():
    """package.json に記載された grammar path が実在するか検証する"""
    pkg = load_json(os.path.join(BASE_DIR, "package.json"))
    grammar_path = pkg["contributes"]["grammars"][0]["path"]
    full_path = os.path.join(BASE_DIR, grammar_path.lstrip("./"))
    assert os.path.isfile(full_path), f"grammar path が存在しません: {grammar_path}"

    config_path = pkg["contributes"]["languages"][0]["configuration"]
    full_cfg_path = os.path.join(BASE_DIR, config_path.lstrip("./"))
    assert os.path.isfile(full_cfg_path), f"configuration path が存在しません: {config_path}"

    print("ok: path consistency")


def main():
    tests = [
        test_package_json,
        test_language_configuration_json,
        test_grammar_json,
        test_grammar_path_consistency,
    ]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"FAIL: {test.__name__}: {e}", file=sys.stderr)
            failed += 1
        except Exception as e:
            print(f"ERROR: {test.__name__}: {e}", file=sys.stderr)
            failed += 1
    if failed:
        sys.exit(1)
    print(f"\n{len(tests)} tests passed")


if __name__ == "__main__":
    main()
