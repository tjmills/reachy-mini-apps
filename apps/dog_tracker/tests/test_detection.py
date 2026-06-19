"""Frame transform and target-selection tests."""

from dataclasses import dataclass

from dog_tracker.detection import PreparedFrame, select_target


@dataclass
class FakeBox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float


@dataclass
class FakeResult:
    label: str
    score: float
    box: FakeBox


def test_select_target_chooses_largest_match_and_maps_coordinates() -> None:
    prepared = PreparedFrame(
        jpeg=b"jpeg",
        scale=0.5,
        crop_x=20,
        crop_y=10,
        frame_width=640,
        frame_height=480,
    )
    results = [
        FakeResult("dog", 0.9, FakeBox(10, 10, 30, 30)),
        FakeResult("dog", 0.8, FakeBox(20, 20, 80, 70)),
        FakeResult("cat", 0.99, FakeBox(0, 0, 100, 100)),
    ]

    detection = select_target(
        results,
        prepared,
        target_label="dog",
        threshold=0.5,
    )

    assert detection is not None
    assert detection.score == 0.8
    assert detection.box.center == (140, 110)


def test_select_target_returns_none_without_matching_label() -> None:
    prepared = PreparedFrame(
        jpeg=b"jpeg",
        scale=1.0,
        crop_x=0,
        crop_y=0,
        frame_width=320,
        frame_height=180,
    )
    result = select_target(
        [FakeResult("cat", 0.9, FakeBox(1, 1, 10, 10))],
        prepared,
        target_label="dog",
        threshold=0.5,
    )
    assert result is None
