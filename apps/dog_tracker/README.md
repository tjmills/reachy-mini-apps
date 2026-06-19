# Dog Tracker

Tracks dogs using remote Hugging Face inference and directs Reachy Mini's gaze
toward detections. The app can also play configured audio reactions.

## Configuration

Copy `.env.example` to `.env` and provide the required Hugging Face endpoint
and authentication values. Never commit `.env`.

## Run

From the repository root:

```bash
make run-local PROJECT=dog_tracker
```

The Reachy Mini daemon must be available and the selected media backend must
support camera frames. Confirm whether testing targets simulation, Lite, or
Wireless hardware before running the app.
