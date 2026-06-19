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
    [ -f "$app_dir/index.html" ] ||
        report_error "$app is missing index.html"
    [ -f "$app_dir/style.css" ] ||
        report_error "$app is missing style.css"

    nested_main_count=$(find "$app_dir" -mindepth 2 -maxdepth 2 -type f -name main.py | wc -l)
    [ "$nested_main_count" -eq 1 ] ||
        report_error "$app needs exactly one <package>/main.py"
    nested_init_count=$(find "$app_dir" -mindepth 2 -maxdepth 2 -type f -name __init__.py | wc -l)
    [ "$nested_init_count" -ge 1 ] ||
        report_error "$app is missing <package>/__init__.py"

    if [ -f "$app_dir/pyproject.toml" ]; then
        grep -q '^\[project\]' "$app_dir/pyproject.toml" ||
            report_error "$app pyproject.toml is missing [project]"
        grep -q '^name[[:space:]]*=' "$app_dir/pyproject.toml" ||
            report_error "$app pyproject.toml is missing project.name"
        grep -q '^requires-python[[:space:]]*=' "$app_dir/pyproject.toml" ||
            report_error "$app pyproject.toml is missing requires-python"
        grep -qi '"reachy-mini' "$app_dir/pyproject.toml" ||
            report_error "$app does not declare a reachy-mini dependency"
        grep -q '^\[project.entry-points."reachy_mini_apps"\]' "$app_dir/pyproject.toml" ||
            report_error "$app does not register a reachy_mini_apps entry point"
    fi

    if [ -f "$app_dir/README.md" ]; then
        grep -q 'reachy_mini_python_app' "$app_dir/README.md" ||
            report_error "$app README is missing the reachy_mini_python_app tag"
        grep -q 'reachy_mini' "$app_dir/README.md" ||
            report_error "$app README is missing the reachy_mini tag"
    fi

    if [ "$nested_main_count" -eq 1 ]; then
        main_file=$(find "$app_dir" -mindepth 2 -maxdepth 2 -type f -name main.py)
        grep -q 'class .*ReachyMiniApp' "$main_file" ||
            report_error "$app main.py does not define a ReachyMiniApp subclass"
    fi

    [ ! -f "$app_dir/uv.lock" ] ||
        report_error "$app has an app-local uv.lock; use the root lockfile"
    [ ! -d "$app_dir/build" ] ||
        report_error "$app contains generated build/ output"
    if find "$app_dir" -maxdepth 1 -type d -name '*.egg-info' | grep -q .; then
        report_error "$app contains generated *.egg-info output"
    fi
done

[ "$count" -gt 0 ] || report_error "no apps found under apps/"

if [ "$errors" -gt 0 ]; then
    printf 'App contract failed: %s error(s) across %s app(s)\n' "$errors" "$count" >&2
    exit 1
fi

printf 'App contract OK: %s app(s)\n' "$count"
