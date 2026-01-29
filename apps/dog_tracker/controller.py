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

    DETECTED = "detected"
    SCANNING = "scanning"


@dataclass
class ControllerState:
    """Internal state for the motion controller."""

    mode: ControlMode = ControlMode.SCANNING
    scan_start_time: float = field(default_factory=time.monotonic)
    last_update_time: float = field(default_factory=time.monotonic)
    current_yaw: float = 0.0
    current_pitch: float = 0.0
    current_body_yaw: float = 0.0


class Controller:
    """Head motion controller for scanning and detection behaviors."""

    # Head joint limits (radians)
    YAW_LIMIT = np.deg2rad(45)
    PITCH_LIMIT = np.deg2rad(30)
    BODY_YAW_LIMIT = np.deg2rad(20)

    # Scanning motion parameters
    BODY_YAW_AMPLITUDE_DEG = 15.0  # Body sweep amplitude
    PITCH_BASE_DEG = 5.0  # Looking slightly down at floor level
    PITCH_VARIATION_DEG = 3.0  # Slight up/down nod

    def __init__(self, config: Config, frame_width: int = 640, frame_height: int = 480):
        self.config = config
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frame_center = (frame_width // 2, frame_height // 2)
        self.state = ControllerState()

    def update(
        self, detection: Detection | None, detection_age: float
    ) -> tuple[float, float, float, bool]:
        """Compute target head position based on detection state.

        Args:
            detection: Current detection (may be None)
            detection_age: Seconds since last valid detection

        Returns:
            Tuple of (yaw, pitch, body_yaw, reaction_triggered).
        """
        # Determine mode based on detection freshness
        if detection is not None and detection_age < self.config.lost_timeout:
            reaction_triggered = self.state.mode != ControlMode.DETECTED
            if reaction_triggered:
                print(f"Detected: {detection.label} (conf={detection.score:.2f})")
                self.state.mode = ControlMode.DETECTED
            return self._detected_update(reaction_triggered)
        else:
            if self.state.mode != ControlMode.SCANNING:
                print("Scanning for target...")
                self.state.mode = ControlMode.SCANNING
                self.state.scan_start_time = time.monotonic()
            return self._scanning_update()

    def _detected_update(self, reaction_triggered: bool) -> tuple[float, float, float, bool]:
        """Freeze position when target detected.

        Returns current position unchanged (robot freezes when it sees target).
        """
        self.state.last_update_time = time.monotonic()
        return (
            float(self.state.current_yaw),
            float(self.state.current_pitch),
            float(self.state.current_body_yaw),
            reaction_triggered,
        )

    def _scanning_update(self) -> tuple[float, float, float, bool]:
        """Compute current scan position from sine wave.

        Called at control_hz (e.g. 30Hz). Always returns the instantaneous
        position — no waypoint interval gating needed since set_target is
        non-blocking.
        """
        now = time.monotonic()
        self.state.last_update_time = now
        elapsed = now - self.state.scan_start_time
        phase = (2 * np.pi * elapsed) / self.config.scan_period

        target_yaw = np.deg2rad(self.config.scan_amplitude_deg) * np.sin(phase)
        target_body_yaw = np.deg2rad(self.BODY_YAW_AMPLITUDE_DEG) * np.sin(phase - 0.3)
        target_pitch = np.deg2rad(
            self.PITCH_BASE_DEG + self.PITCH_VARIATION_DEG * np.sin(phase * 2)
        )
        target_body_yaw = float(
            np.clip(target_body_yaw, -self.BODY_YAW_LIMIT, self.BODY_YAW_LIMIT)
        )

        self.state.current_yaw = float(target_yaw)
        self.state.current_pitch = float(target_pitch)
        self.state.current_body_yaw = target_body_yaw

        return (float(target_yaw), float(target_pitch), target_body_yaw, False)

    def resume_scanning(self) -> None:
        """Reset controller to scanning mode."""
        self.state.mode = ControlMode.SCANNING
        self.state.scan_start_time = time.monotonic()
        print("Resuming scanning...")

    @property
    def mode(self) -> ControlMode:
        """Current operating mode."""
        return self.state.mode
