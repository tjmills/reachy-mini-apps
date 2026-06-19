#!/bin/sh

set +e
uv run --group dev pytest
status=$?
set -e

if [ "$status" -eq 5 ]; then
    printf '%s\n' "No tests collected; add app tests under apps/<name>/ when behavior is testable."
    exit 0
fi

exit "$status"
