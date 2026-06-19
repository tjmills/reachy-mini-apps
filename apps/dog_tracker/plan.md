# Canonicalization plan

## Goal

Turn Dog Tracker into a reference implementation for reactive camera apps.

## Approach

- Package the app using the official `ReachyMiniApp` contract.
- Normalize serverless and dedicated-endpoint results in one detector.
- Run camera capture and inference in one background worker.
- Keep all regular robot output in one 50 Hz main control loop.
- Use calibrated `look_at_image()` poses for detections and bounded sinusoidal
  poses while scanning.
- Play reactions from the output-owning thread, with detection paused.
- Reject stale inference, enforce reaction cooldown, and clean up threads and
  robot state deterministically.
- Unit-test configuration, crop mapping, target selection, and controller state.

## Open questions

None. Physical tuning still requires a Lite or Wireless robot.
