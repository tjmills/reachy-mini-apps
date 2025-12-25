# Target Tracking App

YOLO-based target tracking for Reachy Mini. This app is installable via the Reachy Mini Apps system.

## Install on Reachy Mini
1) Copy this folder to the robot (or clone the repo on the robot).
2) From `apps/target_tracking/`:
```
uv pip install .
```
If `uv` is not available:
```
python -m pip install .
```
3) The app will appear in the Reachy Mini Apps list as `target_tracking`.

## Run from laptop (streaming required)
If you want to run from a laptop, the daemon must be started with `--stream` so WebRTC is enabled.
```
uv run python apps/target_tracking/track_target.py --wireless-version
```

## Configuration (env vars)
- `TARGET_TRACKING_LABEL` (default: `person`)
- `TARGET_TRACKING_CONF` (default: `0.7`)
- `TARGET_TRACKING_HZ` (default: `15.0`)
- `TARGET_TRACKING_MODEL_REPO` (default: empty, let Ultralytics download)
- `TARGET_TRACKING_MODEL_FILE` (default: `yolov8n.pt`)
