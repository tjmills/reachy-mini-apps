"""Tests for camera readiness handling."""

import threading

import numpy as np
from hello_vision.main import wait_for_frame


class FakeMedia:
    def __init__(self, frames: list[np.ndarray | None]) -> None:
        self.frames = iter(frames)

    def get_frame(self) -> np.ndarray | None:
        return next(self.frames)


def test_wait_for_frame_retries_until_frame_is_ready() -> None:
    expected = np.zeros((2, 3, 3), dtype=np.uint8)
    media = FakeMedia([None, None, expected])
    retries: list[int] = []

    actual = wait_for_frame(
        media,
        threading.Event(),
        attempts=3,
        retry_delay=0.0,
        on_retry=retries.append,
    )

    assert actual is expected
    assert retries == [1, 2]


def test_wait_for_frame_rejects_empty_frames() -> None:
    media = FakeMedia([np.array([], dtype=np.uint8)])
    try:
        wait_for_frame(media, threading.Event(), attempts=1, retry_delay=0.0)
    except RuntimeError as error:
        assert "Camera did not produce a frame" in str(error)
    else:
        raise AssertionError("Expected an empty frame to fail")
