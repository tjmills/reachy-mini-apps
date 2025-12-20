# SDK Recipes (Codex workspace)

Workspace-level tips to get coding fast. Use `vendor/reachy_mini/` for deeper API reference.

## Environment + dependencies
```bash
uv venv
uv sync               # installs reachy-mini from PyPI
uv sync --extra mujoco # only if you need simulation/media extras
```

Clone upstream source (read-only, gitignored) if you want to browse docs/examples offline:
```bash
uv run python scripts/clone_vendor.py
```

## Daemon quickstart
- Wireless: robot runs the daemon when powered; connect over LAN with `ReachyMini(localhost_only=False)`.
- Lite on your laptop: `uv run reachy-mini-daemon`
- Simulation: `uv run reachy-mini-daemon --sim` (or `ReachyMini(spawn_daemon=True, use_sim=True)`)
- Verify at `http://localhost:8000` and keep the daemon terminal open.

## Minimal connect-and-move
```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

with ReachyMini(localhost_only=False) as mini:  # set to True if daemon is local
    mini.goto_target(head=create_head_pose(z=10, mm=True, degrees=True), duration=2.0)
```
Run with:
```bash
uv run python apps/hello_motion/main.py  # replace path with your script
```

## Motion patterns
- Smooth interpolation: `mini.goto_target(head=..., antennas=[rad, rad], body_yaw=rad, duration=secs, method="minjerk")`
- Immediate update: `mini.set_target(...)` (no interpolation; use for high-rate control)
- Head pose helper: `create_head_pose(x=0, y=0, z=10, roll=0, pitch=0, yaw=0, mm=True, degrees=True)`

## Media (camera + audio)
```python
frame = mini.media.get_frame()            # OpenCV BGR frame
sample = mini.media.get_audio_sample()    # ndarray of audio samples
mini.media.play_sound("path.wav")         # play file
mini.media.push_audio_sample(sample)      # stream chunk
```
- For wireless over LAN, start daemon with `--stream` to enable WebRTC; otherwise use `media_backend="no_media"` or `default_no_video` when constructing `ReachyMini`.

## Recording and replay
```python
mini.start_recording()
# ... move the robot or send commands ...
recorded = mini.stop_recording()
# recorded is a list of poses/angles you can store or feed back to goto_target
```
