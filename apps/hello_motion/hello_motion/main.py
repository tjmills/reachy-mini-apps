"""Canonical gestures and continuous-motion example for Reachy Mini."""

from __future__ import annotations

import argparse
import logging
import threading
import time
from dataclasses import dataclass

import numpy as np
from reachy_mini import ReachyMini, ReachyMiniApp
from reachy_mini.reachy_mini import INIT_ANTENNAS_JOINT_POSITIONS, INIT_HEAD_POSE
from reachy_mini.utils import create_head_pose

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class MotionConfig:
    """Runtime parameters for the motion demonstration."""

    continuous_duration: float = 6.0
    control_hz: float = 50.0

    def __post_init__(self) -> None:
        if self.continuous_duration <= 0:
            raise ValueError("continuous_duration must be positive")
        if not 30.0 <= self.control_hz <= 100.0:
            raise ValueError("control_hz must be between 30 and 100 Hz")


@dataclass(frozen=True)
class MotionTargets:
    """One sample of the continuous trajectory, expressed in radians."""

    head_pitch: float
    body_yaw: float
    right_antenna: float
    left_antenna: float


def continuous_targets(elapsed: float) -> MotionTargets:
    """Return a conservative, phase-aligned continuous-motion sample."""
    base_phase = 2.0 * np.pi * 0.18 * elapsed
    antenna_phase = 2.0 * np.pi * 0.55 * elapsed
    return MotionTargets(
        head_pitch=float(np.deg2rad(6.0) * np.sin(base_phase)),
        body_yaw=float(np.deg2rad(18.0) * np.sin(base_phase)),
        right_antenna=float(np.deg2rad(25.0) * np.sin(antenna_phase)),
        left_antenna=float(-np.deg2rad(25.0) * np.sin(antenna_phase)),
    )


def return_to_neutral(mini: ReachyMini, duration: float = 1.0) -> None:
    """Leave the robot in a predictable neutral pose."""
    mini.goto_target(
        head=INIT_HEAD_POSE,
        antennas=INIT_ANTENNAS_JOINT_POSITIONS,
        body_yaw=0.0,
        duration=duration,
        method="minjerk",
    )


class HelloMotion(ReachyMiniApp):
    """Demonstrate canonical finite gestures and real-time motion control."""

    custom_app_url = None
    dont_start_webserver = True
    request_media_backend = "no_media"

    def __init__(self, config: MotionConfig | None = None) -> None:
        super().__init__()
        self.config = config or MotionConfig()

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event) -> None:
        """Run the demonstration and respond promptly to app shutdown."""
        reachy_mini.enable_motors()
        return_to_neutral(reachy_mini)

        try:
            self._run_gestures(reachy_mini, stop_event)
            if not stop_event.is_set():
                self._run_continuous_motion(reachy_mini, stop_event)
        finally:
            return_to_neutral(reachy_mini)

    @staticmethod
    def _run_gestures(mini: ReachyMini, stop_event: threading.Event) -> None:
        """Use blocking interpolation for a short sequence of gestures."""
        gestures = [
            (
                create_head_pose(z=12, pitch=8, mm=True),
                np.deg2rad([25.0, -25.0]),
                np.deg2rad(10.0),
            ),
            (
                create_head_pose(z=8, roll=12, pitch=-4, yaw=12, mm=True),
                np.deg2rad([-15.0, 20.0]),
                np.deg2rad(-10.0),
            ),
            (
                create_head_pose(z=8, roll=-12, pitch=-4, yaw=-12, mm=True),
                np.deg2rad([20.0, -15.0]),
                np.deg2rad(10.0),
            ),
        ]

        LOGGER.info("Running three interpolated gestures")
        for head, antennas, body_yaw in gestures:
            if stop_event.is_set():
                return
            mini.goto_target(
                head=head,
                antennas=antennas,
                body_yaw=float(body_yaw),
                duration=0.9,
                method="minjerk",
            )

    def _run_continuous_motion(self, mini: ReachyMini, stop_event: threading.Event) -> None:
        """Own the only `set_target` loop and maintain a fixed update rate."""
        LOGGER.info(
            "Running %.1f seconds of continuous motion at %.0f Hz",
            self.config.continuous_duration,
            self.config.control_hz,
        )
        started = time.monotonic()
        deadline = started
        interval = 1.0 / self.config.control_hz

        while not stop_event.is_set():
            now = time.monotonic()
            elapsed = now - started
            if elapsed >= self.config.continuous_duration:
                break

            targets = continuous_targets(elapsed)
            mini.set_target(
                head=create_head_pose(pitch=targets.head_pitch, degrees=False),
                antennas=[targets.right_antenna, targets.left_antenna],
                body_yaw=targets.body_yaw,
            )

            deadline += interval
            stop_event.wait(max(0.0, deadline - time.monotonic()))


def parse_args() -> argparse.Namespace:
    """Parse options used when running this module directly."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--continuous-duration", type=float, default=6.0)
    parser.add_argument("--control-hz", type=float, default=50.0)
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    """Run the app outside the Reachy Mini dashboard."""
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(name)s: %(message)s",
    )
    app = HelloMotion(
        MotionConfig(
            continuous_duration=args.continuous_duration,
            control_hz=args.control_hz,
        )
    )
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()


if __name__ == "__main__":
    main()
