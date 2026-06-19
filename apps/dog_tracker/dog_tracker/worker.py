"""Background frame capture and inference worker."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Protocol

import numpy as np
import numpy.typing as npt

from .detection import Detection

LOGGER = logging.getLogger(__name__)
Frame = npt.NDArray[np.uint8]


class FrameSource(Protocol):
    def get_frame(self) -> Frame | None:
        """Return the latest camera frame."""


class Detector(Protocol):
    def detect(self, frame: Frame) -> Detection | None:
        """Return the selected target, if present."""


@dataclass(frozen=True)
class DetectionSnapshot:
    """Latest completed inference result."""

    sequence: int = 0
    detection: Detection | None = None
    captured_at: float = 0.0
    error: str | None = None


class DetectionWorker:
    """Own frame capture and remote inference on one background thread."""

    def __init__(
        self,
        source: FrameSource,
        detector: Detector,
        *,
        detection_hz: float,
        max_inference_age: float,
        app_stop_event: threading.Event,
        pause_event: threading.Event,
    ) -> None:
        self.source = source
        self.detector = detector
        self.interval = 1.0 / detection_hz
        self.max_inference_age = max_inference_age
        self.app_stop_event = app_stop_event
        self.pause_event = pause_event
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._snapshot = DetectionSnapshot()
        self._thread = threading.Thread(
            target=self._run,
            name="dog-tracker-inference",
            daemon=False,
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self, timeout: float = 12.0) -> None:
        self._stop_event.set()
        self._thread.join(timeout)
        if self._thread.is_alive():
            LOGGER.warning("Inference worker did not stop within %.1f seconds", timeout)

    def latest(self) -> DetectionSnapshot:
        with self._lock:
            return self._snapshot

    def _should_stop(self) -> bool:
        return self._stop_event.is_set() or self.app_stop_event.is_set()

    def _run(self) -> None:
        sequence = 0
        while not self._should_stop():
            if self.pause_event.is_set():
                self._stop_event.wait(0.05)
                continue

            cycle_started = time.monotonic()
            frame = self.source.get_frame()
            if frame is None or frame.size == 0:
                self._stop_event.wait(0.1)
                continue

            captured_at = time.monotonic()
            try:
                detection = self.detector.detect(frame)
                finished_at = time.monotonic()
                if finished_at - captured_at > self.max_inference_age:
                    detection = None
                    error = "Discarded stale inference result"
                else:
                    error = None
            except Exception as exception:
                detection = None
                error = f"{type(exception).__name__}: {exception}"

            sequence += 1
            with self._lock:
                self._snapshot = DetectionSnapshot(
                    sequence=sequence,
                    detection=detection,
                    captured_at=captured_at,
                    error=error,
                )

            remaining = self.interval - (time.monotonic() - cycle_started)
            if remaining > 0:
                self._stop_event.wait(remaining)
