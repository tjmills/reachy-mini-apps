# Workflow (Codex-friendly)

1) Prep the environment: `uv venv && uv sync` (add `--extra mujoco` if you need sim or Mujoco extras).
2) Confirm platform and daemon plan:
   - Wireless: daemon already on robot -> connect with `localhost_only=False`.
   - Lite: start `uv run reachy-mini-daemon` on your machine.
   - Simulation: `uv run reachy-mini-daemon --sim` or `ReachyMini(spawn_daemon=True, use_sim=True)`.
3) Decide media backend:
   - Local dev: `media_backend="default"` (OpenCV + SoundDevice).
   - Remote wireless: `media_backend="webrtc"` if streaming is enabled, else `"no_media"`.
   - On-device wireless apps: prefer `"gstreamer"`.
4) Build inside `apps/<your_app>/` using the `ReachyMini` context manager.
5) Choose motion style:
   - `goto_target` for smooth, timed moves.
   - `set_target` for high-rate control and streaming control loops.
6) If you use media loops:
   - Camera: read BGR frames via `mini.media.get_frame()`; store in a thread-safe buffer.
   - Audio: start recording/playing, then loop `get_audio_sample()` + `push_audio_sample()`.
   - Always stop loops before `media.close()` and `client.disconnect()`.
7) Provide runnable commands (`uv run python apps/.../main.py`) and quick verification steps (open `http://localhost:8000`, observe motion).
8) When APIs are unclear, read the upstream `reachy_mini` docs/examples/src (or your installed package) before guessing.
9) For SDK changes or “latest” behavior, search https://github.com/pollen-robotics/reachy_mini (code + issues) and summarize any relevant updates before implementing.
