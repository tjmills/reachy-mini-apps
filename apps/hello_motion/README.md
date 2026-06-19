---
title: Hello Motion
emoji: 👋
colorFrom: orange
colorTo: red
sdk: static
pinned: false
short_description: Learn smooth gestures and real-time Reachy Mini control.
tags:
  - reachy_mini
  - reachy_mini_python_app
---

# Hello Motion

A canonical Python example showing the two Reachy Mini motion styles:

- `goto_target()` for smooth, finite gestures.
- `set_target()` from one fixed-rate control loop for continuous motion.

The app uses no camera or audio, enables motors before setting targets, keeps
all commanded angles inside conservative limits, and returns the robot to a
neutral pose when it stops.

## Run

Start a Reachy Mini daemon or simulation, then run from the monorepo root:

```bash
make run-local PROJECT=hello_motion
```

For a Wireless robot configured in the root `Makefile`:

```bash
make sync-up
make run PROJECT=hello_motion
```

The standalone module also accepts:

```bash
uv run --directory apps/hello_motion python -m hello_motion.main \
  --continuous-duration 6 --control-hz 50
```

Simulation can validate the motion sequence. Physical hardware is still
required to judge smoothness, range, and the robot's expressive character.
