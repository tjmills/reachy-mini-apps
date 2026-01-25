"""Dog tracking app for Reachy Mini using remote HuggingFace inference."""

from __future__ import annotations

import time


def main() -> None:
    """Main entry point for dog tracker."""
    # Import inside main so file can be read without deps
    from reachy_mini import ReachyMini  # type: ignore
    import cv2  # type: ignore

    from config import Config

    # Load configuration
    config = Config.from_env()
    print("Dog Tracker starting...")
    print(f"  Model: {config.model}")
    print(f"  Target: {config.target_label} (conf >= {config.confidence_threshold})")

    # Force correct on-robot media backend
    with ReachyMini(media_backend="gstreamer") as mini:
        mini.wake_up()
        print("Connected to Reachy Mini")
        time.sleep(1)

        # Test frame capture like hello_vision (with retries for camera init)
        frame = None
        for attempt in range(5):
            frame = mini.media.get_frame()
            if frame is not None:
                break
            print(f"Waiting for camera... (attempt {attempt + 1}/5)")
            time.sleep(0.5)

        if frame is None:
            print("ERROR: Could not capture frame from camera")
        else:
            frame_height, frame_width = frame.shape[:2]
            print(f"Camera resolution: {frame_width}x{frame_height}")
            cv2.imwrite("./test_frame.png", frame)
            print("Saved test_frame.png")

        mini.goto_sleep()
        print("Dog Tracker stopped.")


if __name__ == "__main__":
    main()
