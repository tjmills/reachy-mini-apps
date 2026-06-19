---
title: Dog Tracker
emoji: 🐕
colorFrom: amber
colorTo: orange
sdk: static
pinned: false
short_description: Track dogs with Reachy Mini and remote vision inference.
tags:
  - reachy_mini
  - reachy_mini_python_app
---

# Dog Tracker

A complete reactive-app example combining Reachy Mini's camera, remote Hugging
Face object detection, calibrated gaze targeting, scanning motion, and recorded
emotion playback.

The architecture follows the Reachy control-loop guidance:

- One worker owns frame capture and remote inference.
- One fixed-rate loop is the only normal caller of `set_target()`.
- New detections are converted to head poses with `look_at_image()`.
- Recorded reactions temporarily take ownership of robot output in the same
  main thread, so commands never race.
- Monotonic timing, stale-result rejection, cooldown, and deterministic cleanup
  keep the behavior stable.

## Configuration

Copy `.env.example` to `.env` and provide a Hugging Face token:

```bash
cp apps/dog_tracker/.env.example apps/dog_tracker/.env
```

The token must be able to call the configured model or dedicated endpoint.
Never commit `.env`.

## Run

```bash
make run-local PROJECT=dog_tracker
```

For a Wireless robot:

```bash
make sync-up
make run PROJECT=dog_tracker
```

This app requires physical camera hardware; simulation cannot test detection,
audio, or real motor behavior. Before running it, confirm that no other process
owns the camera and that the robot has network access to Hugging Face.

## Important settings

- `DOG_TRACKER_MODEL`: serverless object-detection model.
- `DOG_TRACKER_ENDPOINT_URL`: optional dedicated inference endpoint.
- `DOG_TRACKER_LABEL`: target label, default `dog`.
- `DOG_TRACKER_CONF`: confidence threshold from 0 to 1.
- `DOG_TRACKER_DETECTION_HZ`: remote inference frequency.
- `DOG_TRACKER_CONTROL_HZ`: robot output frequency, 30–100 Hz.
- `DOG_TRACKER_REACTION_EMOTION`: recorded move played on acquisition.
- `DOG_TRACKER_REACTION_AUDIO`: packaged WAV file overriding move audio.
- `DOG_TRACKER_REACTION_COOLDOWN`: minimum seconds between reactions.
