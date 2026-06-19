"""Validated environment configuration for Dog Tracker."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    try:
        return default if value is None else float(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a number, got {value!r}") from error


@dataclass(frozen=True)
class TrackerConfig:
    """All runtime settings needed by the tracker."""

    hf_token: str
    model: str = "hustvl/yolos-tiny"
    target_label: str = "dog"
    confidence_threshold: float = 0.5
    detection_hz: float = 2.0
    control_hz: float = 50.0
    lost_timeout: float = 2.0
    scan_amplitude_deg: float = 25.0
    scan_period: float = 6.0
    endpoint_url: str | None = None
    reaction_emotion: str = "surprised1"
    reaction_audio: str | None = None
    reaction_cooldown: float = 15.0
    max_inference_age: float = 4.0
    inference_timeout: float = 10.0

    def __post_init__(self) -> None:
        if not self.hf_token:
            raise ValueError("HF_TOKEN is required")
        if not self.target_label.strip():
            raise ValueError("DOG_TRACKER_LABEL cannot be empty")
        if not 0.0 < self.confidence_threshold <= 1.0:
            raise ValueError("DOG_TRACKER_CONF must be in (0, 1]")
        if not 0.1 <= self.detection_hz <= 10.0:
            raise ValueError("DOG_TRACKER_DETECTION_HZ must be between 0.1 and 10")
        if not 30.0 <= self.control_hz <= 100.0:
            raise ValueError("DOG_TRACKER_CONTROL_HZ must be between 30 and 100")
        if self.lost_timeout <= 0:
            raise ValueError("DOG_TRACKER_LOST_TIMEOUT must be positive")
        if not 0.0 < self.scan_amplitude_deg <= 35.0:
            raise ValueError("DOG_TRACKER_SCAN_AMPLITUDE_DEG must be in (0, 35]")
        if self.scan_period <= 0:
            raise ValueError("DOG_TRACKER_SCAN_PERIOD must be positive")
        if self.reaction_cooldown < 0:
            raise ValueError("DOG_TRACKER_REACTION_COOLDOWN cannot be negative")
        if self.max_inference_age <= 0:
            raise ValueError("max_inference_age must be positive")
        if self.inference_timeout <= 0:
            raise ValueError("inference_timeout must be positive")
        if self.reaction_audio is not None:
            audio_name = Path(self.reaction_audio)
            if audio_name.name != self.reaction_audio:
                raise ValueError("DOG_TRACKER_REACTION_AUDIO must be a packaged filename")

    @classmethod
    def from_env(cls) -> TrackerConfig:
        """Load `.env` and process environment variables."""
        load_dotenv()
        return cls(
            hf_token=os.environ.get("HF_TOKEN", ""),
            model=os.environ.get("DOG_TRACKER_MODEL", "hustvl/yolos-tiny"),
            target_label=os.environ.get("DOG_TRACKER_LABEL", "dog"),
            confidence_threshold=_env_float("DOG_TRACKER_CONF", 0.5),
            detection_hz=_env_float("DOG_TRACKER_DETECTION_HZ", 2.0),
            control_hz=_env_float("DOG_TRACKER_CONTROL_HZ", 50.0),
            lost_timeout=_env_float("DOG_TRACKER_LOST_TIMEOUT", 2.0),
            scan_amplitude_deg=_env_float("DOG_TRACKER_SCAN_AMPLITUDE_DEG", 25.0),
            scan_period=_env_float("DOG_TRACKER_SCAN_PERIOD", 6.0),
            endpoint_url=os.environ.get("DOG_TRACKER_ENDPOINT_URL") or None,
            reaction_emotion=os.environ.get("DOG_TRACKER_REACTION_EMOTION", "surprised1"),
            reaction_audio=os.environ.get("DOG_TRACKER_REACTION_AUDIO") or None,
            reaction_cooldown=_env_float("DOG_TRACKER_REACTION_COOLDOWN", 15.0),
        )
