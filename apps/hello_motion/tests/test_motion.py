"""Tests for the hardware-independent motion trajectory."""

import numpy as np
from hello_motion.main import MotionConfig, continuous_targets


def test_continuous_targets_stay_inside_conservative_limits() -> None:
    for elapsed in np.linspace(0.0, 12.0, 200):
        targets = continuous_targets(float(elapsed))
        assert abs(np.rad2deg(targets.head_pitch)) <= 6.0
        assert abs(np.rad2deg(targets.body_yaw)) <= 18.0
        assert abs(np.rad2deg(targets.right_antenna)) <= 25.0
        assert abs(np.rad2deg(targets.left_antenna)) <= 25.0


def test_motion_config_rejects_slow_control_loops() -> None:
    try:
        MotionConfig(control_hz=20.0)
    except ValueError as error:
        assert "between 30 and 100" in str(error)
    else:
        raise AssertionError("Expected invalid control frequency to fail")
