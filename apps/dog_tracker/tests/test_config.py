"""Configuration validation tests."""

from dog_tracker.config import TrackerConfig


def test_config_rejects_slow_robot_control() -> None:
    try:
        TrackerConfig(hf_token="token", control_hz=20.0)
    except ValueError as error:
        assert "between 30 and 100" in str(error)
    else:
        raise AssertionError("Expected slow control loop to fail")


def test_config_rejects_reaction_path_traversal() -> None:
    try:
        TrackerConfig(hf_token="token", reaction_audio="../secret.wav")
    except ValueError as error:
        assert "packaged filename" in str(error)
    else:
        raise AssertionError("Expected path traversal to fail")
