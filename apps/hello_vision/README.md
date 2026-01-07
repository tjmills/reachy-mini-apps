# hello_vision

Minimal macOS app to verify Reachy Mini camera streaming.

## Run
```bash
uv run python apps/hello_vision/main.py --no-localhost-only --backend webrtc
```

## Notes
- Requires the Reachy Mini daemon to be running.
- For a robot on your LAN, pass `--no-localhost-only --backend webrtc`.
- Press `q` or `Esc` to quit the window.
- If macOS prompts for camera access, allow it for your terminal app.
- If `--backend webrtc` fails, install GStreamer WebRTC deps (Homebrew example):
  `brew install gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly libnice`
