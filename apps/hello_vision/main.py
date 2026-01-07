"""Reachy Mini camera sanity check for macOS.

Opens a window with live frames from the robot camera and prints FPS.
Press "q" or Esc to quit.
"""

from __future__ import annotations

import argparse
from argparse import BooleanOptionalAction
import subprocess
import sys
import time

def main() -> None:

    from reachy_mini import ReachyMini  # type: ignore
    import cv2  # type: ignore


    print(
        "Connecting to Reachy Mini "
    )
    with ReachyMini(
        media_backend="default"
    ) as mini:
        frame = mini.media.get_frame()
        print(frame)
        cv2.imwrite("./test", frame)


if __name__ == "__main__":
    main()
