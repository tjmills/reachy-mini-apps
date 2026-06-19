#!/bin/sh

set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
errors=0
count=0

report_error() {
    printf 'app contract error: %s\n' "$1" >&2
    errors=$((errors + 1))
}

for app_dir in "$root"/apps/*; do
    [ -d "$app_dir" ] || continue
    app=$(basename "$app_dir")
    count=$((count + 1))

    [ -f "$app_dir/pyproject.toml" ] ||
        report_error "$app is missing pyproject.toml"
    [ -f "$app_dir/README.md" ] ||
        report_error "$app is missing README.md"
    if [ ! -f "$app_dir/main.py" ]; then
        nested_main_count=$(find "$app_dir" -mindepth 2 -maxdepth 2 -type f -name main.py | wc -l)
        [ "$nested_main_count" -eq 1 ] ||
            report_error "$app needs one entry point at main.py or <package>/main.py"
    fi

    if [ -f "$app_dir/pyproject.toml" ]; then
        grep -q '^\[project\]' "$app_dir/pyproject.toml" ||
            report_error "$app pyproject.toml is missing [project]"
        grep -q '^name[[:space:]]*=' "$app_dir/pyproject.toml" ||
            report_error "$app pyproject.toml is missing project.name"
        grep -q '^requires-python[[:space:]]*=' "$app_dir/pyproject.toml" ||
            report_error "$app pyproject.toml is missing requires-python"
        grep -qi '"reachy-mini' "$app_dir/pyproject.toml" ||
            report_error "$app does not declare a reachy-mini dependency"
    fi

    [ ! -f "$app_dir/uv.lock" ] ||
        report_error "$app has an app-local uv.lock; use the root lockfile"
done

[ "$count" -gt 0 ] || report_error "no apps found under apps/"

if [ "$errors" -gt 0 ]; then
    printf 'App contract failed: %s error(s) across %s app(s)\n' "$errors" "$count" >&2
    exit 1
fi

printf 'App contract OK: %s app(s)\n' "$count"
