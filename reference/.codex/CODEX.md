# Workspace guidance for Codex — Reachy Mini SDK

This repo is a scratchpad for building new Reachy Mini apps with Codex. Use the upstream clone in `vendor/reachy_mini/` as read-only reference; runtime packages come from `uv sync`.

## Layout + etiquette
- `apps/` is the only place you should add runnable code by default.
- `reference/` holds Codex notes and prompt templates (keep them concise and actionable).
- `vendor/reachy_mini/` mirrors the SDK source; never edit it unless the user asks.
- If an API surface is unclear, open `vendor/reachy_mini/src/` or `vendor/reachy_mini/docs/SDK/`.

## Talking to the robot/sim
- The daemon must be running. Wireless: powered robot already runs it. Lite: `uv run reachy-mini-daemon`. Simulation: `uv run reachy-mini-daemon --sim` (or `ReachyMini(spawn_daemon=True, use_sim=True)`).
- Default client only connects to localhost (`ReachyMini()` → Zenoh at `tcp/localhost:7447`). For wireless/LAN robots use `ReachyMini(localhost_only=False)` to enable discovery.
- Prefer the context manager to clean up media and sockets:
```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

with ReachyMini(localhost_only=False) as mini:
    mini.goto_target(head=create_head_pose(z=10, mm=True, degrees=True), duration=1.5)
```
- Media: camera/audio live under `mini.media` (OpenCV frames, sounddevice audio). Remote streaming needs the daemon `--stream` flag; otherwise set `media_backend="no_media"` or `default_no_video`.

## When writing answers
- Confirm platform (Wireless | Lite | Simulation), where the script runs, and whether to start/stop the daemon.
- Emit runnable code plus the exact `uv run ...` commands, and note required extras (e.g., `--extra mujoco` for sim).
- Call out safety defaults: radians vs degrees, mm vs meters, `goto_target` vs `set_target`, and `localhost_only` behavior.

## High-signal references (browse in this order)
1) `reference/docs/ASK_CODEX_PROMPT.md` (what details to request from the user)
2) `vendor/reachy_mini/README.md`
3) `vendor/reachy_mini/docs/SDK/` (installation, quickstart, python-sdk)
4) `vendor/reachy_mini/examples/`
