"""Capture and save one frame from Reachy Mini's camera."""

from __future__ import annotations

import argparse
import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np
import numpy.typing as npt
from reachy_mini import ReachyMini, ReachyMiniApp

LOGGER = logging.getLogger(__name__)
Frame = npt.NDArray[np.uint8]


class FrameProvider(Protocol):
    """Minimal media interface needed by this example."""

    def get_frame(self) -> Frame | None:
        """Return the latest camera frame, if one is ready."""


def wait_for_frame(
    media: FrameProvider,
    stop_event: threading.Event,
    *,
    attempts: int,
    retry_delay: float,
    on_retry: Callable[[int], None] | None = None,
) -> Frame:
    """Wait for a valid camera frame or raise a clear error."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if retry_delay < 0:
        raise ValueError("retry_delay cannot be negative")

    for attempt in range(1, attempts + 1):
        if stop_event.is_set():
            raise InterruptedError("Frame capture stopped before a frame was available")

        frame = media.get_frame()
        if frame is not None and frame.size > 0:
            return frame

        if on_retry is not None:
            on_retry(attempt)
        stop_event.wait(retry_delay)

    raise RuntimeError(
        "Camera did not produce a frame. Check that the daemon is running, "
        "the selected media backend is available, and no other app owns the camera."
    )


class HelloVision(ReachyMiniApp):
    """Canonical single-frame camera capture app."""

    custom_app_url = None
    dont_start_webserver = True
    request_media_backend = "default"

    def __init__(
        self,
        *,
        output: Path = Path("captures/reachy-mini-frame.png"),
        attempts: int = 10,
        retry_delay: float = 0.5,
        backend: str = "default",
    ) -> None:
        self.request_media_backend = backend
        super().__init__()
        self.output = output
        self.attempts = attempts
        self.retry_delay = retry_delay

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event) -> None:
        """Capture one frame without commanding unrelated robot motion."""
        frame = wait_for_frame(
            reachy_mini.media,
            stop_event,
            attempts=self.attempts,
            retry_delay=self.retry_delay,
            on_retry=lambda attempt: LOGGER.info(
                "Waiting for camera frame (%s/%s)", attempt, self.attempts
            ),
        )

        output = self.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(output), frame):
            raise RuntimeError(f"OpenCV failed to write camera frame to {output}")

        height, width = frame.shape[:2]
        LOGGER.info("Saved %sx%s camera frame to %s", width, height, output)


def parse_args() -> argparse.Namespace:
    """Parse direct-run options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend",
        choices=("default", "local", "webrtc"),
        default="default",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("captures/reachy-mini-frame.png"),
    )
    parser.add_argument("--attempts", type=int, default=10)
    parser.add_argument("--retry-delay", type=float, default=0.5)
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    """Run the app outside the dashboard."""
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(name)s: %(message)s",
    )
    app = HelloVision(
        output=args.output,
        attempts=args.attempts,
        retry_delay=args.retry_delay,
        backend=args.backend,
    )
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()


if __name__ == "__main__":
    main()
