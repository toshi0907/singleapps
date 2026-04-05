#!/usr/bin/env sh
set -eu

actual="$("$(dirname "$0")/../src/hello.sh")"
expected="helloworld"

if [ "$actual" != "$expected" ]; then
  echo "test failed: expected '$expected' but got '$actual'" >&2
  exit 1
fi

echo "ok"
