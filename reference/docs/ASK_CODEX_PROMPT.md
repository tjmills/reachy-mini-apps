# Ask-Codex Prompt Template (Reachy Mini)

Use this repo as context; `vendor/reachy_mini/` is read-only reference for API details.

When you ask Codex for help, include:
- Task: <what to build/run>
- Platform: Wireless | Lite | Simulation
- Where code runs vs daemon: <robot / my laptop / container> and daemon start command if relevant
- Connection: localhost-only? LAN? (Wireless needs `localhost_only=False`)
- Subsystems needed: motion | camera | audio (and whether streaming is required)
- Safety/limits: any motion bounds, units (deg vs rad, mm vs m), recording permission

What to expect from Codex
- Runnable code with sensible defaults and comments where the SDK is non-obvious.
- Exact commands to run (`uv run ...`) plus notes if sim extras (`--extra mujoco`) are needed.
- Quick troubleshooting: daemon not running, wrong host, streaming disabled, missing `sounddevice`/OpenCV permissions.
