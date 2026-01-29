"""Configuration for dog tracker app via environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Dog tracker configuration loaded from environment variables."""

    hf_token: str
    model: str = "hustvl/yolos-tiny"
    target_label: str = "dog"
    confidence_threshold: float = 0.5
    detection_hz: float = 2.0
    control_hz: float = 30.0
    lost_timeout: float = 2.0  # seconds before switching to scanning (accounts for HF latency)
    scan_amplitude_deg: float = 25.0
    scan_period: float = 6.0
    endpoint_url: str | None = None  # HF Inference Endpoint URL (optional, for lower latency)
    # Reaction configuration
    reaction_emotion: str = "angry"  # emotion name from EMOTIONS dict
    reaction_sound_hz: int = 440  # beep frequency
    reaction_sound_duration: float = 0.3  # beep length in seconds
    scan_only_duration: float = 60.0  # seconds of scan-only after a reaction

    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from environment variables."""
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN environment variable is required")

        return cls(
            hf_token=hf_token,
            model=os.environ.get("DOG_TRACKER_MODEL", "hustvl/yolos-tiny"),
            target_label=os.environ.get("DOG_TRACKER_LABEL", "dog"),
            confidence_threshold=float(os.environ.get("DOG_TRACKER_CONF", "0.5")),
            detection_hz=float(os.environ.get("DOG_TRACKER_HZ", "2.0")),
            endpoint_url=os.environ.get("DOG_TRACKER_ENDPOINT_URL"),
            reaction_emotion=os.environ.get("DOG_TRACKER_REACTION_EMOTION", "angry"),
            reaction_sound_hz=int(os.environ.get("DOG_TRACKER_REACTION_SOUND_HZ", "440")),
            reaction_sound_duration=float(os.environ.get("DOG_TRACKER_REACTION_SOUND_DURATION", "0.3")),
            scan_only_duration=float(os.environ.get("DOG_TRACKER_SCAN_ONLY_DURATION", "60.0")),
        )
