"""Head motion controller for dog tracking and scanning."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from config import Config
    from detector import Detection


class ControlMode(Enum):
    """Controller operating mode."""

    TRACKING = "tracking"
    SCANNING = "scanning"


@dataclass
class ControllerState:
    """Internal state for the motion controller."""

    mode: ControlMode = ControlMode.SCANNING
    scan_start_time: float = field(default_factory=time.monotonic)
    smoothed_yaw: float = 0.0
    smoothed_pitch: float = 0.0


class Controller:
    """Head motion controller for tracking and scanning behaviors."""

    # Proportional gains for tracking
    YAW_KP = 0.025
    PITCH_KP = 0.020

    # Dead band to prevent jitter (pixels from center)
    DEAD_BAND = 20

    # EMA smoothing factor (higher = more responsive, lower = smoother)
    SMOOTHING_ALPHA = 0.7

    # Head joint limits (radians)
    YAW_LIMIT = np.deg2rad(45)
    PITCH_LIMIT = np.deg2rad(30)

    def __init__(self, config: Config, frame_width: int = 640, frame_height: int = 480):
        self.config = config
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frame_center = (frame_width // 2, frame_height // 2)
        self.state = ControllerState()

    def update(
        self, detection: Detection | None, detection_age: float
    ) -> tuple[float, float, float]:
        """Compute target head position based on detection state.

        Args:
            detection: Current detection (may be None)
            detection_age: Seconds since last valid detection

        Returns:
            Tuple of (yaw, pitch, body_yaw) in radians
        """
        # Determine mode based on detection freshness
        if detection is not None and detection_age < self.config.lost_timeout:
            if self.state.mode != ControlMode.TRACKING:
                print(f"Tracking: {detection.label} (conf={detection.score:.2f})")
                self.state.mode = ControlMode.TRACKING
            return self._tracking_update(detection)
        else:
            if self.state.mode != ControlMode.SCANNING:
                print("Scanning for target...")
                self.state.mode = ControlMode.SCANNING
                self.state.scan_start_time = time.monotonic()
            return self._scanning_update()

    def _tracking_update(self, detection: Detection) -> tuple[float, float, float]:
        """Compute tracking motion to center detection in frame."""
        cx, cy = detection.center
        fx, fy = self.frame_center

        # Error from center (positive error = target to the right/below)
        error_x = cx - fx
        error_y = cy - fy

        # Apply dead band
        if abs(error_x) < self.DEAD_BAND:
            error_x = 0
        if abs(error_y) < self.DEAD_BAND:
            error_y = 0

        # Proportional control (negate because yaw left = positive, camera right = positive error)
        target_yaw = -error_x * self.YAW_KP
        target_pitch = -error_y * self.PITCH_KP

        # EMA smoothing
        self.state.smoothed_yaw = (
            self.SMOOTHING_ALPHA * target_yaw
            + (1 - self.SMOOTHING_ALPHA) * self.state.smoothed_yaw
        )
        self.state.smoothed_pitch = (
            self.SMOOTHING_ALPHA * target_pitch
            + (1 - self.SMOOTHING_ALPHA) * self.state.smoothed_pitch
        )

        # Clamp to joint limits
        yaw = np.clip(self.state.smoothed_yaw, -self.YAW_LIMIT, self.YAW_LIMIT)
        pitch = np.clip(self.state.smoothed_pitch, -self.PITCH_LIMIT, self.PITCH_LIMIT)

        # No body rotation during tracking (head only)
        return float(yaw), float(pitch), 0.0

    def _scanning_update(self) -> tuple[float, float, float]:
        """Compute scanning motion to sweep the room."""
        elapsed = time.monotonic() - self.state.scan_start_time
        phase = (2 * np.pi * elapsed) / self.config.scan_period

        # Sinusoidal yaw sweep
        yaw = np.deg2rad(self.config.scan_amplitude_deg) * np.sin(phase)

        # Slight downward pitch to look at floor level (where dogs typically are)
        pitch = np.deg2rad(5.0)

        # Reset smoothed values during scanning
        self.state.smoothed_yaw = float(yaw)
        self.state.smoothed_pitch = float(pitch)

        return float(yaw), float(pitch), 0.0

    @property
    def mode(self) -> ControlMode:
        """Current operating mode."""
        return self.state.mode
