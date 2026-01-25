"""
Simple example to take a frame with Reachy Mini.
Must be run on the robot (Wireless).
"""
from __future__ import annotations

import time


def main() -> None:
    from reachy_mini import ReachyMini  # type: ignore
    import cv2  # type: ignore

    # Force correct on-robot media backend
    with ReachyMini(media_backend="gstreamer") as mini:
        # Bring head out
        mini.wake_up()
        time.sleep(1.0)  # let the motion finish + camera settle

        # Capture frame
        frame = mini.media.get_frame()
        if frame is None:
            raise RuntimeError(
                "Camera returned None — camera likely owned by another app "
                "(dashboard) or gstreamer pipeline not ready."
            )

        cv2.imwrite("./test.png", frame)

        # Optional but polite
        mini.goto_sleep()


if __name__ == "__main__":
    main()
