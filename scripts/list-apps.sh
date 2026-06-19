#!/bin/sh

set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

for app_dir in "$root"/apps/*; do
    [ -d "$app_dir" ] || continue
    [ -f "$app_dir/pyproject.toml" ] || continue
    basename "$app_dir"
done
