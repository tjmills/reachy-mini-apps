#!/bin/sh

set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
sdk="$root/../reachy_mini"

fail() {
    printf 'agent scaffold error: %s\n' "$1" >&2
    exit 1
}

[ -f "$root/AGENTS.md" ] || fail "missing AGENTS.md"
[ -f "$sdk/AGENTS.md" ] || fail "missing sibling SDK guide: $sdk/AGENTS.md"
[ -d "$sdk/skills" ] || fail "missing sibling SDK skills: $sdk/skills"
[ -L "$root/skills" ] || fail "skills must be a symlink to ../reachy_mini/skills"
[ "$(readlink "$root/skills")" = "../reachy_mini/skills" ] ||
    fail "skills points to an unexpected location"

skill_count=0
for source_skill in "$sdk"/skills/*.md; do
    [ -f "$source_skill" ] || continue
    skill_name=$(basename "$source_skill")
    [ -f "$root/skills/$skill_name" ] || fail "shared skill is not exposed: $skill_name"
    skill_count=$((skill_count + 1))
done

[ "$skill_count" -gt 0 ] || fail "no shared skills found"

if [ ! -f "$root/agents.local.md" ]; then
    printf '%s\n' "agent scaffold warning: agents.local.md is absent; run the shared setup playbook"
fi

printf 'Agent scaffold OK: %s shared skills from %s\n' "$skill_count" "$sdk"
