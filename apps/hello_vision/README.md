---
title: Hello Vision
emoji: 📷
colorFrom: blue
colorTo: cyan
sdk: static
pinned: false
short_description: Capture a camera frame from Reachy Mini robustly.
tags:
  - reachy_mini
  - reachy_mini_python_app
---

# Hello Vision

A minimal camera example that relies on the SDK's automatic media backend
selection, waits for the video pipeline to become ready, validates the frame,
and checks that OpenCV actually wrote the output file.

The app does not wake or move the robot because image capture does not require
motion.

## Run

```bash
make run-local PROJECT=hello_vision
```

By default the image is written to `captures/reachy-mini-frame.png`, which is
ignored by Git. Direct execution supports backend and output overrides:

```bash
uv run --directory apps/hello_vision python -m hello_vision.main \
  --backend default \
  --output captures/example.png \
  --attempts 10
```

Available backends are `default`, `local`, and `webrtc`. Prefer `default`; only
override it when diagnosing a known media transport issue.

Camera capture cannot be validated in simulation. Test this example with Lite
or Wireless hardware and ensure no other process owns the camera.
