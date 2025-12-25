# SDK Recipes (Codex workspace)

Workspace-level tips to get coding fast. Use the upstream `reachy_mini` repo (or your installed package) for API reference and `reachy_mini_conversation_app` for app patterns (camera/audio threads, shutdown, settings UI).

## Environment + dependencies
```bash
uv venv
uv sync                # installs reachy-mini from PyPI
uv sync --extra mujoco # only if you need simulation or mujoco extras
```

Clone upstream source (read-only, gitignored) if you want to browse docs/examples offline:
```bash
uv run python scripts/clone_vendor.py
```

## Daemon quickstart
- Wireless: daemon runs on the robot; connect over LAN with `ReachyMini(localhost_only=False)`.
- Lite on your laptop: `uv run reachy-mini-daemon`.
- Simulation: `uv run reachy-mini-daemon --sim` (or `ReachyMini(spawn_daemon=True, use_sim=True)`).
- Verify at `http://localhost:8000` and keep the daemon terminal open.

## Connection + media backend selection
```python
from reachy_mini import ReachyMini

# Local daemon (default media: OpenCV + SoundDevice)
with ReachyMini(localhost_only=True, media_backend="default") as mini:
    ...

# Wireless LAN (remote): request WebRTC explicitly, or disable media
with ReachyMini(localhost_only=False, media_backend="webrtc") as mini:
    ...
```
Notes:
- If `localhost_only=False` and `media_backend="default"`, the SDK checks daemon status and may switch to WebRTC or disable media.
- Use `media_backend="no_media"` or `"default_no_video"` if video/audio is not needed or streaming is unavailable.
- For on-device wireless apps, `ReachyMiniApp` defaults to `gstreamer`.

## Minimal connect-and-move
```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

with ReachyMini(localhost_only=False) as mini:  # set True if daemon is local
    mini.goto_target(head=create_head_pose(z=10, mm=True, degrees=True), duration=2.0)
```
Run with:
```bash
uv run python apps/hello_motion/main.py  # replace path with your script
```

## Motion patterns
- Smooth interpolation: `mini.goto_target(head=..., antennas=[rad, rad], body_yaw=rad, duration=sec, method="minjerk")`.
- Immediate update: `mini.set_target(...)` for high-frequency control.
- Pose helper: `create_head_pose(x, y, z, roll, pitch, yaw, mm=True, degrees=True)`.
- Body yaw: pass `body_yaw=None` to keep the current yaw in `goto_target`.

## Look-at helpers (camera + world)
```python
# Look at a pixel in the camera image (requires camera + intrinsics)
mini.look_at_image(u, v, duration=0.5)

# Look at a 3D point in the world frame (meters)
mini.look_at_world(x=0.5, y=0.0, z=0.2, duration=1.0)
```
Tip: pass `perform_movement=False` to get a pose without moving, then blend it into your own control loop.

## Media (camera + audio)
```python
frame = mini.media.get_frame()            # BGR uint8 frame
sample = mini.media.get_audio_sample()    # float32 array
mini.media.play_sound("wake_up.wav")     # play from assets or absolute path
mini.media.start_playing()                # open output stream
mini.media.push_audio_sample(sample)      # stream chunk
```
Notes:
- `get_audio_sample()` returns float32 arrays; use `mini.media.start_recording()` first when needed.
- `push_audio_sample()` expects float32 mono or multi-channel arrays; MediaManager reshapes to match output channels.

## Recording and replay
```python
mini.start_recording()
# ... move the robot or send commands ...
recorded = mini.stop_recording()
```
- `recorded` is a list of dict frames with timestamps and target data.
- For playback, build a `Move` (see `reachy_mini.motion`) and call `mini.play_move(move)`.

## Move classes and playback
- `Move` defines `duration` and `evaluate(t) -> (head_pose, antennas, body_yaw)`.
- `GotoMove` provides interpolated trajectories.
- `RecordedMove` and `RecordedMoves` can load moves from a Hugging Face dataset and interpolate between frames.

## App scaffolding pattern (ReachyMiniApp)
```python
import threading
from reachy_mini import ReachyMiniApp, ReachyMini

class MyApp(ReachyMiniApp):
    custom_app_url = "http://0.0.0.0:8042"  # optional settings UI
    request_media_backend = None            # or "gstreamer", "default", ...

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            # control loop
            ...

if __name__ == "__main__":
    app = MyApp()
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()
```
- `wrapped_run()` sets up the media backend and optional settings webserver.
- `settings_app` is a FastAPI instance you can mount endpoints on (see app templates).

## Vendor patterns worth copying
- Camera worker thread with a lock-protected latest-frame buffer (conversation app camera worker).
- Audio record/play async loops with resampling and clean shutdown (conversation app console).
- Always stop tasks, then close media, then disconnect the client.
