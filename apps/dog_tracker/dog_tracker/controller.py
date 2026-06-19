"""Pure state machine for scanning, tracking, and reaction requests."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
import numpy.typing as npt
from reachy_mini.utils import create_head_pose

from .config import TrackerConfig


class ControlMode(Enum):
    """Current high-level behavior."""

    SCANNING = "scanning"
    TRACKING = "tracking"


@dataclass(frozen=True)
class ControlCommand:
    """One output sample for the robot-control loop."""

    head: npt.NDArray[np.float64]
    body_yaw: float
    mode: ControlMode


class TrackingController:
    """Maintain tracking freshness, scanning phase, and reaction cooldown."""

    BODY_AMPLITUDE_DEG = 12.0
    SCAN_PITCH_BASE_DEG = 5.0
    SCAN_PITCH_AMPLITUDE_DEG = 3.0

    def __init__(self, config: TrackerConfig, *, started_at: float) -> None:
        self.config = config
        self.mode = ControlMode.SCANNING
        self.scan_started_at = started_at
        self.last_seen_at = float("-inf")
        self.last_reaction_at = float("-inf")
        self.tracking_pose: npt.NDArray[np.float64] | None = None
        self.reaction_pending = False

    def observe(
        self,
        pose: npt.NDArray[np.float64],
        *,
        observed_at: float,
    ) -> None:
        """Record a calibrated target pose from a fresh detection."""
        reacquired = observed_at - self.last_seen_at >= self.config.lost_timeout
        self.tracking_pose = pose
        self.last_seen_at = observed_at
        if reacquired and observed_at - self.last_reaction_at >= self.config.reaction_cooldown:
            self.reaction_pending = True

    def command(self, now: float) -> ControlCommand:
        """Return the current tracking or scanning target."""
        if self.tracking_pose is not None and now - self.last_seen_at < self.config.lost_timeout:
            self.mode = ControlMode.TRACKING
            return ControlCommand(
                head=self.tracking_pose.copy(),
                body_yaw=0.0,
                mode=self.mode,
            )

        if self.mode is not ControlMode.SCANNING:
            self.scan_started_at = now
        self.mode = ControlMode.SCANNING
        elapsed = now - self.scan_started_at
        phase = 2.0 * np.pi * elapsed / self.config.scan_period
        yaw = self.config.scan_amplitude_deg * np.sin(phase)
        pitch = self.SCAN_PITCH_BASE_DEG + self.SCAN_PITCH_AMPLITUDE_DEG * np.sin(2.0 * phase)
        body_yaw = np.deg2rad(self.BODY_AMPLITUDE_DEG * np.sin(phase - 0.25))
        return ControlCommand(
            head=create_head_pose(yaw=float(yaw), pitch=float(pitch)),
            body_yaw=float(body_yaw),
            mode=self.mode,
        )

    def consume_reaction(self, now: float) -> bool:
        """Consume at most one reaction request per target acquisition."""
        if not self.reaction_pending:
            return False
        self.reaction_pending = False
        self.last_reaction_at = now
        return True

    def reset_after_reaction(self, now: float) -> None:
        """Discard stale tracking state and restart scanning."""
        self.mode = ControlMode.SCANNING
        self.scan_started_at = now
        self.last_seen_at = float("-inf")
        self.tracking_pose = None
        self.reaction_pending = False
