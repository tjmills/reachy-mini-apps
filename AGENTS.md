# Repository Guidelines

## Project Structure & Module Organization
- `apps/` holds runnable mini-apps. Each app typically has its own folder (e.g., `apps/hello_motion/`) with a `main.py` entrypoint and an optional `README.md`.
- `scripts/` contains helper utilities such as `scripts/clone_vendor.py` for pulling a local SDK reference.
- `reference/` stores project docs and Codex guidance; treat it as reference material rather than runtime code.
- `vendor/reachy_mini/` is a gitignored clone of the upstream SDK for read-only context.

## Build, Test, and Development Commands
- `uv venv` + `uv sync`: create the virtual environment and install dependencies.
- `uv sync --extra mujoco`: add simulation extras if you need Mujoco.
- `uv run python apps/hello_motion/main.py`: run an app directly.
- `make setup`, `make sync`, `make run-hello`: wrappers for the commands above.
- `make clone-vendor`: populate `vendor/reachy_mini/` for local reference.
- `make lint`: run Ruff for style and import checks.
- `make typecheck`: run MyPy over `apps/` and `scripts/`.

## Coding Style & Naming Conventions
- Python-only repo; use 4-space indentation and keep lines to 100 chars (Ruff config).
- Prefer `snake_case` for modules and functions; app folders should be descriptive (e.g., `apps/target_tracking/`).
- Keep `main.py` as the runnable entrypoint for each app.

## Testing Guidelines
- There are no first-party tests in this workspace yet. If adding tests, use `pytest` and place them under a top-level `tests/` or per-app `tests/` folder.
- Only run vendor SDK tests if you explicitly intend to validate the upstream clone.

## SDK + Vendor Reference Notes (Reachy Mini)
- Primary API entrypoints live in `vendor/reachy_mini/src/reachy_mini/reachy_mini.py` and `vendor/reachy_mini/src/reachy_mini/__init__.py`.
- `ReachyMini(...)` constructor:
  - Connection: `localhost_only` (LAN needs `False`), `spawn_daemon`, `use_sim`, `timeout`.
  - Motion config: `automatic_body_yaw` (daemon-controlled yaw coupling).
  - Media config: `media_backend` in {`default`, `gstreamer`, `webrtc`, `no_media`, `default_no_video`}.
  - If `localhost_only=False` and `media_backend="default"`, the SDK checks daemon status; it switches to WebRTC only if streaming is enabled, otherwise disables media.
- Context manager: `with ReachyMini(...) as mini:` automatically closes media and disconnects the client on exit.
- Core motion APIs:
  - `goto_target(head=pose_4x4, antennas=[r,l], body_yaw=rad, duration=sec, method=InterpolationTechnique)`.
  - `set_target(...)` for immediate updates (useful for high-rate control loops).
  - `look_at_image(u, v, duration, perform_movement)` computes a pose using camera intrinsics (requires camera specs) and delegates to `look_at_world`.
  - `look_at_world(x, y, z, duration, perform_movement)` computes a target pose in the world frame.
  - `get_current_head_pose()`, `get_current_joint_positions()` are the readbacks for closed-loop logic.
- Pose utilities:
  - `reachy_mini.utils.create_head_pose(x, y, z, roll, pitch, yaw, mm=True, degrees=True)` returns a 4x4 pose matrix.
  - Interpolation helpers and method names live in `reachy_mini.utils.interpolation`.
- Motors + compliance:
  - `enable_motors(ids=None)` / `disable_motors(ids=None)` toggle torque.
  - `enable_gravity_compensation()` / `disable_gravity_compensation()` for compliant head motion.
- Recording + playback:
  - `start_recording()` and `stop_recording()` return a list of time-stamped target frames.
  - `play_move(move)` accepts any `Move` subclass; `GotoMove` and `RecordedMove` are examples in `reachy_mini.motion`.
- Media layer (`ReachyMini.media` returns `MediaManager`):
  - `get_frame()` returns BGR `uint8` frames (OpenCV format).
  - Camera intrinsics: `media.camera.K`/`D` and `CameraResolution` in `reachy_mini.media.camera_constants`.
  - Audio I/O: `start_recording()`, `get_audio_sample()` (float32 array), `start_playing()`, `push_audio_sample()`.
  - `play_sound("wake_up.wav")` resolves against `reachy_mini/assets` if a relative path is used.

## App Framework Patterns (SDK)
- `ReachyMiniApp` (in `vendor/reachy_mini/src/reachy_mini/apps/app.py`) is the standard app base class:
  - Override `run(self, reachy_mini, stop_event)`.
  - `wrapped_run()` handles media setup and optional settings webserver.
  - `custom_app_url` + `settings_app` let you mount a small FastAPI settings UI.
  - `request_media_backend` forces a backend; otherwise, wireless defaults to GStreamer.
- The app templates in `vendor/reachy_mini/src/reachy_mini/apps/templates/` show the expected structure and settings endpoint wiring.

## Conversation-App Reference Patterns (vendor/reachy_mini_conversation_app)
- Threaded camera loop with a lock-protected "latest frame" buffer is in `src/reachy_mini_conversation_app/camera_worker.py`.
- Face/head tracking uses `look_at_image(..., perform_movement=False)` to compute a pose and derive offsets without moving the robot; it then smoothly interpolates offsets back to neutral when tracking stops.
- Audio streaming loops (record + play) use `media.get_audio_sample()` and `media.push_audio_sample()` with resampling to match output rates (`src/reachy_mini_conversation_app/console.py`).
- Graceful shutdown pattern: stop threads/tasks first, then `media.close()`, then `client.disconnect()`.

## Commit & Pull Request Guidelines
- Recent history favors short, lowercase commit summaries (e.g., "dance party app"). Keep messages concise and app-focused.
- PRs should include a brief description, how to run the app, and any hardware/simulation assumptions. Add screenshots or short clips for UI/vision demos.

## Security & Configuration Tips
- The Reachy Mini daemon must be running (real hardware or simulation) for most SDK calls.
- Avoid committing the `vendor/reachy_mini/` clone; it is for local reference only.
- For “latest” SDK behavior or breaking changes, search https://github.com/pollen-robotics/reachy_mini (including issues) before deciding on an approach.

## SDK 1.2.4 Remote Media Notes (Wireless)
- **Observed failure:** `reachy-mini==1.2.4` on the client can crash with `ModuleNotFoundError: gst_signalling` or `ValueError: Namespace GstWebRTC not available` when using `localhost_only=False` / `media_backend="webrtc"` for remote wireless control.
- **Quick workaround:** Downgrade the client SDK to `reachy-mini==1.2.3` for Python programs; this restores remote usage without extra GStreamer setup.
- **If staying on 1.2.4:** Install `reachy-mini[gstreamer]` and system GStreamer deps (via `apt`, not pip), then ensure the WebRTC plugin is available. Some systems required compiling `gst-plugins-rs` (`gst-plugin-webrtc`) and setting `GST_PLUGIN_PATH` (use the correct architecture path).
- **Streaming flag:** On 1.2.4, the daemon no longer uses `--stream`; adding it can prevent the robot from booting correctly.
- **Recovery tips:** If `KeyError: 'Producer reachymini not found.'` appears, reboot the robot. If media fails after sleep/wake cycles, a full reset may be needed.
