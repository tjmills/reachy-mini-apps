"""Controller state and safety tests."""

import numpy as np
from dog_tracker.config import TrackerConfig
from dog_tracker.controller import ControlMode, TrackingController


def test_controller_scans_within_configured_limits() -> None:
    config = TrackerConfig(hf_token="token", scan_amplitude_deg=20.0)
    controller = TrackingController(config, started_at=10.0)

    for now in np.linspace(10.0, 20.0, 100):
        command = controller.command(float(now))
        assert command.mode is ControlMode.SCANNING
        assert abs(np.rad2deg(command.body_yaw)) <= controller.BODY_AMPLITUDE_DEG


def test_reaction_is_requested_once_per_acquisition() -> None:
    config = TrackerConfig(hf_token="token", reaction_cooldown=10.0)
    controller = TrackingController(config, started_at=0.0)
    pose = np.eye(4)

    controller.observe(pose, observed_at=1.0)
    assert controller.consume_reaction(1.0)
    assert not controller.consume_reaction(1.1)

    controller.reset_after_reaction(2.0)
    controller.observe(pose, observed_at=5.0)
    assert not controller.consume_reaction(5.0)

    controller.reset_after_reaction(12.0)
    controller.observe(pose, observed_at=12.0)
    assert controller.consume_reaction(12.0)
