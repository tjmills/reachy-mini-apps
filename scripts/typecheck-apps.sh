#!/bin/sh

set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

for app in "$root"/apps/*; do
    [ -d "$app" ] || continue
    [ -f "$app/pyproject.toml" ] || continue
    printf 'Type-checking %s\n' "$(basename "$app")"
    uv run --group dev mypy "$app"
done
