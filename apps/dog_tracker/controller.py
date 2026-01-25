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
    last_update_time: float = field(default_factory=time.monotonic)
    current_yaw: float = 0.0
    current_pitch: float = 0.0
    target_yaw: float = 0.0
    target_pitch: float = 0.0


class Controller:
    """Head motion controller for tracking and scanning behaviors."""

    # Proportional gains for tracking (converts pixel error to radians)
    YAW_KP = 0.002
    PITCH_KP = 0.002

    # Dead band to prevent jitter (pixels from center)
    DEAD_BAND = 30

    # EMA smoothing factor (higher = more responsive, lower = smoother)
    SMOOTHING_ALPHA = 0.15

    # Rate limiting (max radians per second change) for smooth motion
    MAX_YAW_RATE = np.deg2rad(60)  # 60 deg/sec max
    MAX_PITCH_RATE = np.deg2rad(40)  # 40 deg/sec max

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
        now = time.monotonic()
        dt = now - self.state.last_update_time
        self.state.last_update_time = now

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
        # This gives desired delta from current position
        raw_target_yaw = self.state.current_yaw - error_x * self.YAW_KP
        raw_target_pitch = self.state.current_pitch - error_y * self.PITCH_KP

        # EMA smoothing on target
        self.state.target_yaw = (
            self.SMOOTHING_ALPHA * raw_target_yaw
            + (1 - self.SMOOTHING_ALPHA) * self.state.target_yaw
        )
        self.state.target_pitch = (
            self.SMOOTHING_ALPHA * raw_target_pitch
            + (1 - self.SMOOTHING_ALPHA) * self.state.target_pitch
        )

        # Rate limiting: move current toward target at max rate
        max_yaw_delta = self.MAX_YAW_RATE * dt
        max_pitch_delta = self.MAX_PITCH_RATE * dt

        yaw_diff = self.state.target_yaw - self.state.current_yaw
        pitch_diff = self.state.target_pitch - self.state.current_pitch

        self.state.current_yaw += np.clip(yaw_diff, -max_yaw_delta, max_yaw_delta)
        self.state.current_pitch += np.clip(pitch_diff, -max_pitch_delta, max_pitch_delta)

        # Clamp to joint limits
        self.state.current_yaw = np.clip(self.state.current_yaw, -self.YAW_LIMIT, self.YAW_LIMIT)
        self.state.current_pitch = np.clip(self.state.current_pitch, -self.PITCH_LIMIT, self.PITCH_LIMIT)

        # No body rotation during tracking (head only)
        return float(self.state.current_yaw), float(self.state.current_pitch), 0.0

    def _scanning_update(self) -> tuple[float, float, float]:
        """Compute scanning motion to sweep the room."""
        now = time.monotonic()
        dt = now - self.state.last_update_time
        self.state.last_update_time = now

        elapsed = now - self.state.scan_start_time
        phase = (2 * np.pi * elapsed) / self.config.scan_period

        # Sinusoidal yaw sweep
        target_yaw = np.deg2rad(self.config.scan_amplitude_deg) * np.sin(phase)

        # Slight downward pitch to look at floor level (where dogs typically are)
        target_pitch = np.deg2rad(5.0)

        # Rate limiting for smooth transition into scanning
        max_yaw_delta = self.MAX_YAW_RATE * dt
        max_pitch_delta = self.MAX_PITCH_RATE * dt

        yaw_diff = target_yaw - self.state.current_yaw
        pitch_diff = target_pitch - self.state.current_pitch

        self.state.current_yaw += np.clip(yaw_diff, -max_yaw_delta, max_yaw_delta)
        self.state.current_pitch += np.clip(pitch_diff, -max_pitch_delta, max_pitch_delta)

        # Update target state for smooth mode transitions
        self.state.target_yaw = float(target_yaw)
        self.state.target_pitch = float(target_pitch)

        return float(self.state.current_yaw), float(self.state.current_pitch), 0.0

    @property
    def mode(self) -> ControlMode:
        """Current operating mode."""
        return self.state.mode
