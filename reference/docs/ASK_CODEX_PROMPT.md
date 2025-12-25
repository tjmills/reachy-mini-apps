# Ask-Codex Prompt Template (Reachy Mini)

Use this repo as context; `vendor/reachy_mini/` and `vendor/reachy_mini_conversation_app/` are read-only references for SDK APIs and app patterns.

When you ask Codex for help, include:
- Task: what to build/run, and whether it is a script or an app (ReachyMiniApp).
- Platform: Wireless | Lite | Simulation (and whether code runs on robot or laptop).
- Daemon plan: how it is started and where (`uv run reachy-mini-daemon`, `--sim`, or already running on the robot).
- Connection: `localhost_only=True/False`, any known robot IP/hostname, and whether LAN discovery is needed.
- Media needs: camera | audio | both | none; desired backend (`default`, `gstreamer`, `webrtc`, `no_media`).
- Streaming: if remote video/audio is required, confirm daemon streaming status and SDK version constraints.
- Motion constraints: degrees vs radians, mm vs meters, any bounds or safety limits.
- Control style: `goto_target` (smooth) vs `set_target` (high-rate), body_yaw usage, recording needs.
- Shutdown expectations: how to stop threads/tasks and whether to release media explicitly.
- Repo research: instruct Codex to search the Reachy Mini upstream repo (including issues) for SDK updates before answering.

What to expect from Codex
- Runnable code with safe defaults and minimal loops.
- Exact commands to run (`uv run python ...`) plus notes for sim extras (`--extra mujoco`).
- SDK-aware patterns (context manager usage, media backend selection, stop_event handling).
- Quick troubleshooting: daemon not running, wrong host, streaming disabled, missing `sounddevice` or camera permissions.
- Up-to-date notes after checking https://github.com/pollen-robotics/reachy_mini (code + issues) for recent SDK changes.
