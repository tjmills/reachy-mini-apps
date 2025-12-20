# Workflow (Codex-friendly)

1) Prep the environment: `uv venv && uv sync` (add `--extra mujoco` if you need sim/media extras).
2) Confirm the platform and daemon plan:
   - Wireless: daemon already on the robot → connect with `localhost_only=False`
   - Lite: start `uv run reachy-mini-daemon`
   - Simulation: `uv run reachy-mini-daemon --sim` or `ReachyMini(spawn_daemon=True, use_sim=True)`
3) Build inside `apps/<your_app>/`. Use the `ReachyMini` context manager, set `localhost_only` correctly, and prefer `goto_target` for smooth moves.
4) If you need camera/audio over LAN, ensure the daemon runs with `--stream` or choose `media_backend="no_media"` to avoid hangs.
5) Provide runnable commands (`uv run python apps/.../main.py`) and short verification steps (e.g., open `http://localhost:8000`, watch antennas move).
6) When APIs are unclear, read `vendor/reachy_mini/docs/SDK/*.md`, `examples/`, or `src/reachy_mini/` before guessing.
