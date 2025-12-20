# Reachy Mini Workspace (template)

This repo is **your workspace** for building apps on top of the Reachy Mini SDK.

- **Runtime dependency**: installed via `uv` from PyPI (`reachy-mini`).
- **Reference source clone**: `vendor/reachy_mini/` (gitignored). Claude Code can read it for context.
- **Codex workspace notes** live in `reference/.codex/` (committed).

## Quickstart

### 1) Install uv
- See https://docs.astral.sh/uv/ for installation options.

### 2) Create venv + install deps
```bash
uv venv
uv sync
```

### 3) (Optional) install simulation extras
```bash
uv sync --extra mujoco
```

### 4) Clone the SDK source for read-only reference (recommended for Claude Code)
```bash
mkdir -p vendor
git clone https://github.com/pollen-robotics/reachy_mini.git vendor/reachy_mini
```

### 5) Run an example app
```bash
uv run python apps/hello_motion/main.py
```

## Daemon reminder
Most SDK operations require the Reachy Mini daemon to be running (real robot or simulation).

## Repo layout
- `apps/` - your runnable projects
- `reference/` - docs and Claude Code guidance (committed)
- `vendor/` - gitignored clone of the upstream repo for browsing/reference
- `scripts/` - helper scripts (clone vendor, etc.)
