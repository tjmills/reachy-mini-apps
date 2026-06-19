---
title: Hello Emotion
emoji: 🎭
colorFrom: purple
colorTo: pink
sdk: static
pinned: false
short_description: Play synchronized recorded emotions on Reachy Mini.
tags:
  - reachy_mini
  - reachy_mini_python_app
---

# Hello Emotion

Loads the official recorded-emotions dataset and plays a curated sequence using
`ReachyMini.play_move()`. Motion and the move's associated sound are started by
the SDK as one behavior; the app does not manually duplicate audio playback.

## Run

```bash
make run-local PROJECT=hello_emotion
```

Run the module directly for optional controls:

```bash
# List installed/cached moves without connecting to a robot
uv run --directory apps/hello_emotion python -m hello_emotion.main --list

# Play selected moves once
uv run --directory apps/hello_emotion python -m hello_emotion.main \
  --emotions curious1,welcoming1,cheerful1

# Disable associated sounds or loop until interrupted
uv run --directory apps/hello_emotion python -m hello_emotion.main --no-sound --loop
```

The app validates requested names, enables motors before playback, honors the
dashboard stop event between moves, cancels playback during cleanup, and returns
to neutral.

Simulation can exercise recorded motion but cannot validate physical character
or audio output.
