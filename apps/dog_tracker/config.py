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
    lost_timeout: float = 1.5
    scan_amplitude_deg: float = 25.0
    scan_period: float = 6.0

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
        )
