"""Remote object detection using HuggingFace Inference API."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

import cv2
import numpy as np
from huggingface_hub import AsyncInferenceClient

if TYPE_CHECKING:
    from config import Config


@dataclass
class Detection:
    """A detected object with bounding box and metadata."""

    label: str
    score: float
    box: tuple[int, int, int, int]  # (x_min, y_min, x_max, y_max)

    @property
    def center(self) -> tuple[int, int]:
        """Return center point of the bounding box."""
        x_min, y_min, x_max, y_max = self.box
        return ((x_min + x_max) // 2, (y_min + y_max) // 2)

    @property
    def area(self) -> int:
        """Return area of the bounding box."""
        x_min, y_min, x_max, y_max = self.box
        return (x_max - x_min) * (y_max - y_min)


class Detector:
    """Async remote object detector using HuggingFace Inference API."""

    def __init__(self, config: Config):
        self.config = config
        self.client = AsyncInferenceClient(model=config.model, token=config.hf_token)
        self._last_detection: Detection | None = None
        self._last_detection_time: float = 0.0
        self._pending_task: asyncio.Task | None = None

    def _encode_frame(self, frame: np.ndarray) -> bytes:
        """Encode frame as JPEG bytes for API transmission."""
        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not success:
            raise RuntimeError("Failed to encode frame as JPEG")
        return buffer.tobytes()

    async def _detect_async(self, frame: np.ndarray) -> Detection | None:
        """Run object detection on frame and return best matching detection."""
        jpeg_bytes = self._encode_frame(frame)

        try:
            results = await self.client.object_detection(jpeg_bytes)
        except Exception as e:
            print(f"Detection API error: {e}")
            return None

        # Filter for target label with sufficient confidence
        detections = []
        for result in results:
            # Skip results with missing label
            if result.label is None:
                continue
            if (
                result.label.lower() == self.config.target_label.lower()
                and result.score >= self.config.confidence_threshold
            ):
                box = result.box
                detections.append(
                    Detection(
                        label=result.label,
                        score=result.score,
                        box=(int(box.xmin), int(box.ymin), int(box.xmax), int(box.ymax)),
                    )
                )

        if not detections:
            return None

        # Return largest detection (likely closest/most prominent)
        return max(detections, key=lambda d: d.area)

    def submit_frame(self, frame: np.ndarray) -> None:
        """Submit a frame for async detection (non-blocking)."""
        # Don't submit if a detection is already in progress
        if self._pending_task is not None and not self._pending_task.done():
            return

        self._pending_task = asyncio.create_task(self._detect_async(frame))

    def get_detection(self) -> tuple[Detection | None, float]:
        """Get the most recent detection and its age in seconds.

        Returns:
            Tuple of (detection, age_seconds). Detection may be None if
            no target has been detected yet.
        """
        # Check if pending task completed
        if self._pending_task is not None and self._pending_task.done():
            try:
                result = self._pending_task.result()
                if result is not None:
                    self._last_detection = result
                    self._last_detection_time = time.monotonic()
            except Exception as e:
                print(f"Detection task error: {e}")
            self._pending_task = None

        if self._last_detection_time > 0:
            age = time.monotonic() - self._last_detection_time
        else:
            age = float("inf")
        return self._last_detection, age

    def clear_detection(self) -> None:
        """Clear cached detection (e.g., when entering scan mode)."""
        self._last_detection = None
        self._last_detection_time = 0.0
