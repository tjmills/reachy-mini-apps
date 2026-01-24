# Reachy Mini Apps

Monorepo of tutorial and demo applications for Reachy Mini, an open-source desktop humanoid robot by Pollen Robotics (acquired by Hugging Face, April 2025).

## Reachy Mini Hardware

- 11"/28cm tall desktop humanoid robot
- 6 DOF head movement, body rotation, 2 animated antennas
- Wide-angle camera, 4 microphones, 5W speaker
- **Wireless version**: Raspberry Pi 4 internal compute, WiFi, accelerometer
- Python SDK: `reachy-mini`

## Project Structure

```
reachy_mini_apps/
├── apps/
│   ├── hello_motion/     # Motion control tutorial
│   ├── hello_vision/     # Camera streaming demo
│   └── target_tracking/  # YOLO-based tracking
├── pyproject.toml        # Root workspace config
└── .claude/claude.md
```

## Development Workflow

**Primary workflow: Apps run on robot**

```bash
# Sync from laptop to robot
make -C apps/hello_motion sync PROJECT=hello_motion

# Run on robot via SSH
make -C apps/hello_motion run

# Or SSH and run directly
ssh pollen@reachy-mini.local
cd /home/pollen/projects/hello_motion
/opt/uv/uv run python main.py
```

**Robot connection:**
- Host: `pollen@reachy-mini.local`
- Remote path: `/home/pollen/projects/`
- Python on robot: `/opt/uv/uv run python`

## Package Manager

Uses `uv` - fast Python package manager.

```bash
# Sync workspace dependencies
uv sync

# Sync specific app
cd apps/hello_motion && uv sync

# On robot
/opt/uv/uv sync
```

## Code Style

- Python 3.10 (required by reachy-mini SDK)
- Line length: 100
- Linting: ruff (rules: E, F, I, B, UP; ignore: E203)
- Type checking: mypy (disallow_untyped_defs=false)

## App Notes

### hello_motion
- Demonstrates: antenna wiggle, head poses, sinusoidal motion
- Media backend: `no_media` (no camera needed)

### hello_vision
- Demonstrates: camera frame capture
- Media backend: `default` (uses GStreamer on robot)
- Outputs `test.png`

### target_tracking
- YOLO object detection and tracking
- Env vars: `TARGET_TRACKING_LABEL`, `TARGET_TRACKING_CONF`, `TARGET_TRACKING_HZ`, `TARGET_TRACKING_MODEL_FILE`
- Installable as Reachy Mini app
