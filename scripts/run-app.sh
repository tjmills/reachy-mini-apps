#!/bin/sh

set -eu

if [ "$#" -lt 1 ]; then
    printf '%s\n' "Usage: scripts/run-app.sh <app-directory> [arguments...]" >&2
    exit 2
fi

app_dir=$1
shift

[ -d "$app_dir" ] || {
    printf 'Unknown app directory: %s\n' "$app_dir" >&2
    exit 1
}

if [ -f "$app_dir/main.py" ]; then
    entrypoint=main.py
else
    entrypoints=$(find "$app_dir" -mindepth 2 -maxdepth 2 -type f -name main.py)
    entrypoint_count=$(printf '%s\n' "$entrypoints" | grep -c .)
    [ "$entrypoint_count" -eq 1 ] || {
        printf 'Expected one <package>/main.py entry point in %s\n' "$app_dir" >&2
        exit 1
    }
    entrypoint=${entrypoints#"$app_dir/"}
fi

cd "$app_dir"
exec "${UV:-uv}" run python "$entrypoint" "$@"
