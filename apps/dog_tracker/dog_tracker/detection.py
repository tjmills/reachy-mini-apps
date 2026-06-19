"""Frame preparation and Hugging Face object detection."""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, cast

import cv2
import numpy as np
import numpy.typing as npt
import requests  # type: ignore[import-untyped]
from huggingface_hub import InferenceClient

from .config import TrackerConfig

Frame = npt.NDArray[np.uint8]


@dataclass(frozen=True)
class BoundingBox:
    """Bounding box in original camera-frame coordinates."""

    xmin: int
    ymin: int
    xmax: int
    ymax: int

    @property
    def center(self) -> tuple[int, int]:
        return ((self.xmin + self.xmax) // 2, (self.ymin + self.ymax) // 2)

    @property
    def area(self) -> int:
        return max(0, self.xmax - self.xmin) * max(0, self.ymax - self.ymin)


@dataclass(frozen=True)
class Detection:
    """Normalized object detection."""

    label: str
    score: float
    box: BoundingBox
    frame_width: int
    frame_height: int


@dataclass(frozen=True)
class PreparedFrame:
    """Encoded crop plus the transform back to the original frame."""

    jpeg: bytes
    scale: float
    crop_x: int
    crop_y: int
    frame_width: int
    frame_height: int


@dataclass(frozen=True)
class RawDetection:
    """Transport-independent detection result in crop coordinates."""

    label: str
    score: float
    xmin: float
    ymin: float
    xmax: float
    ymax: float


def prepare_frame(
    frame: Frame,
    *,
    target_width: int = 320,
    crop_width: int = 240,
    crop_height: int = 180,
    jpeg_quality: int = 75,
) -> PreparedFrame:
    """Resize, center-crop, and JPEG-encode a camera frame."""
    if frame.size == 0 or frame.ndim < 2:
        raise ValueError("Camera frame is empty")

    frame_height, frame_width = frame.shape[:2]
    scale = target_width / frame_width
    resized_height = max(1, int(round(frame_height * scale)))
    resized = cv2.resize(frame, (target_width, resized_height))

    actual_crop_width = min(crop_width, target_width)
    actual_crop_height = min(crop_height, resized_height)
    crop_x = (target_width - actual_crop_width) // 2
    crop_y = (resized_height - actual_crop_height) // 2
    cropped = resized[
        crop_y : crop_y + actual_crop_height,
        crop_x : crop_x + actual_crop_width,
    ]

    success, encoded = cv2.imencode(
        ".jpg",
        cropped,
        [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality],
    )
    if not success:
        raise RuntimeError("OpenCV failed to encode the camera frame")

    return PreparedFrame(
        jpeg=encoded.tobytes(),
        scale=scale,
        crop_x=crop_x,
        crop_y=crop_y,
        frame_width=frame_width,
        frame_height=frame_height,
    )


def _raw_detection(result: Any) -> RawDetection:
    """Normalize dict and huggingface_hub result objects."""
    if isinstance(result, dict):
        box = result["box"]
        return RawDetection(
            label=str(result["label"]),
            score=float(result["score"]),
            xmin=float(box["xmin"]),
            ymin=float(box["ymin"]),
            xmax=float(box["xmax"]),
            ymax=float(box["ymax"]),
        )

    box = result.box
    return RawDetection(
        label=str(result.label),
        score=float(result.score),
        xmin=float(box.xmin),
        ymin=float(box.ymin),
        xmax=float(box.xmax),
        ymax=float(box.ymax),
    )


def select_target(
    results: Sequence[Any],
    prepared: PreparedFrame,
    *,
    target_label: str,
    threshold: float,
) -> Detection | None:
    """Return the largest matching detection mapped to camera coordinates."""
    matches: list[Detection] = []
    for result in results:
        raw = _raw_detection(result)
        if raw.label.casefold() != target_label.casefold() or raw.score < threshold:
            continue

        def original_x(value: float) -> int:
            return int(np.clip((value + prepared.crop_x) / prepared.scale, 0, prepared.frame_width))

        def original_y(value: float) -> int:
            return int(
                np.clip((value + prepared.crop_y) / prepared.scale, 0, prepared.frame_height)
            )

        matches.append(
            Detection(
                label=raw.label,
                score=raw.score,
                box=BoundingBox(
                    xmin=original_x(raw.xmin),
                    ymin=original_y(raw.ymin),
                    xmax=original_x(raw.xmax),
                    ymax=original_y(raw.ymax),
                ),
                frame_width=prepared.frame_width,
                frame_height=prepared.frame_height,
            )
        )

    return max(matches, key=lambda detection: detection.box.area, default=None)


class InferenceDetector:
    """Synchronous detector used by the background inference worker."""

    def __init__(self, config: TrackerConfig) -> None:
        self.config = config
        self.client = InferenceClient(
            provider="hf-inference",
            token=config.hf_token,
            timeout=config.inference_timeout,
        )
        self.session = requests.Session()

    def detect(self, frame: Frame) -> Detection | None:
        """Run remote inference and normalize the best matching result."""
        prepared = prepare_frame(frame)
        if self.config.endpoint_url:
            results = self._detect_endpoint(prepared.jpeg)
        else:
            results = cast(
                Sequence[Any],
                self.client.object_detection(
                    prepared.jpeg,
                    model=self.config.model,
                    threshold=self.config.confidence_threshold,
                ),
            )
        return select_target(
            results,
            prepared,
            target_label=self.config.target_label,
            threshold=self.config.confidence_threshold,
        )

    def _detect_endpoint(self, jpeg: bytes) -> Sequence[Any]:
        """Call a dedicated endpoint with bounded scale-up retries."""
        assert self.config.endpoint_url is not None
        wait = 1.0
        for attempt in range(4):
            response = self.session.post(
                self.config.endpoint_url,
                headers={
                    "Authorization": f"Bearer {self.config.hf_token}",
                    "Content-Type": "image/jpeg",
                },
                data=jpeg,
                timeout=self.config.inference_timeout,
            )
            if response.status_code != 503 or attempt == 3:
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, list):
                    raise RuntimeError("Inference endpoint returned a non-list response")
                return cast(Sequence[Any], payload)
            time.sleep(wait)
            wait = min(wait * 2.0, 8.0)

        raise RuntimeError("Inference endpoint did not return a result")
