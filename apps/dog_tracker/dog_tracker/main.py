"""Track dogs with Reachy Mini using remote Hugging Face inference."""

from __future__ import annotations

import argparse
import logging
import threading
import time
from pathlib import Path

from reachy_mini import ReachyMini, ReachyMiniApp
from reachy_mini.motion.recorded_move import RecordedMoves
from reachy_mini.reachy_mini import INIT_ANTENNAS_JOINT_POSITIONS, INIT_HEAD_POSE

from .config import TrackerConfig
from .controller import ControlMode, TrackingController
from .detection import InferenceDetector
from .worker import DetectionWorker

LOGGER = logging.getLogger(__name__)
EMOTIONS_DATASET = "pollen-robotics/reachy-mini-emotions-library"


def return_to_neutral(mini: ReachyMini, duration: float = 1.0) -> None:
    """Leave the robot in a predictable neutral pose."""
    mini.goto_target(
        head=INIT_HEAD_POSE,
        antennas=INIT_ANTENNAS_JOINT_POSITIONS,
        body_yaw=0.0,
        duration=duration,
        method="minjerk",
    )


class DogTracker(ReachyMiniApp):
    """Canonical reactive camera-tracking app."""

    custom_app_url = None
    dont_start_webserver = True
    request_media_backend = "default"

    def __init__(self, config: TrackerConfig | None = None) -> None:
        super().__init__()
        self._config = config

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event) -> None:
        """Run inference and robot output with clear thread ownership."""
        config = self._config or TrackerConfig.from_env()
        detector = InferenceDetector(config)
        controller = TrackingController(config, started_at=time.monotonic())
        pause_event = threading.Event()
        worker = DetectionWorker(
            reachy_mini.media,
            detector,
            detection_hz=config.detection_hz,
            max_inference_age=config.max_inference_age,
            app_stop_event=stop_event,
            pause_event=pause_event,
        )
        emotions = RecordedMoves(EMOTIONS_DATASET)
        if config.reaction_emotion not in emotions.list_moves():
            raise ValueError(
                f"Recorded move {config.reaction_emotion!r} is unavailable in {EMOTIONS_DATASET}"
            )

        reachy_mini.enable_motors()
        reachy_mini.set_automatic_body_yaw(False)
        return_to_neutral(reachy_mini)
        worker.start()

        interval = 1.0 / config.control_hz
        deadline = time.monotonic()
        last_sequence = 0
        last_error: str | None = None
        last_mode: ControlMode | None = None

        LOGGER.info(
            "Tracking %r at %.1f inference Hz and %.0f control Hz",
            config.target_label,
            config.detection_hz,
            config.control_hz,
        )

        try:
            while not stop_event.is_set():
                now = time.monotonic()
                snapshot = worker.latest()
                if snapshot.sequence != last_sequence:
                    last_sequence = snapshot.sequence
                    if snapshot.error and snapshot.error != last_error:
                        LOGGER.warning("Inference: %s", snapshot.error)
                        last_error = snapshot.error
                    elif snapshot.detection is not None:
                        last_error = None
                        detection = snapshot.detection
                        u, v = detection.box.center
                        u = max(1, min(detection.frame_width - 1, u))
                        v = max(1, min(detection.frame_height - 1, v))
                        pose = reachy_mini.look_at_image(
                            u,
                            v,
                            duration=0.0,
                            perform_movement=False,
                        )
                        controller.observe(pose, observed_at=snapshot.captured_at)

                if controller.consume_reaction(now):
                    pause_event.set()
                    self._play_reaction(reachy_mini, emotions, config)
                    controller.reset_after_reaction(time.monotonic())
                    pause_event.clear()
                    deadline = time.monotonic()
                    continue

                command = controller.command(now)
                if command.mode is not last_mode:
                    LOGGER.info("Control mode: %s", command.mode.value)
                    last_mode = command.mode

                reachy_mini.set_target(
                    head=command.head,
                    antennas=INIT_ANTENNAS_JOINT_POSITIONS,
                    body_yaw=command.body_yaw,
                )

                deadline += interval
                stop_event.wait(max(0.0, deadline - time.monotonic()))
        finally:
            pause_event.set()
            worker.stop()
            reachy_mini.cancel_move()
            reachy_mini.set_automatic_body_yaw(True)
            return_to_neutral(reachy_mini)

    @staticmethod
    def _play_reaction(
        mini: ReachyMini,
        emotions: RecordedMoves,
        config: TrackerConfig,
    ) -> None:
        """Play one reaction while the main thread owns robot output."""
        LOGGER.info("Reacting with %s", config.reaction_emotion)
        move = emotions.get(config.reaction_emotion)
        if config.reaction_audio:
            audio_path = Path(__file__).parent / "assets" / config.reaction_audio
            if not audio_path.is_file():
                raise FileNotFoundError(f"Packaged reaction audio not found: {audio_path}")
            mini.media.play_sound(str(audio_path))
            mini.play_move(move, initial_goto_duration=0.8, sound=False)
        else:
            mini.play_move(move, initial_goto_duration=0.8, sound=True)


def parse_args() -> argparse.Namespace:
    """Parse direct-run options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    """Run the app outside the dashboard."""
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app = DogTracker()
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()


if __name__ == "__main__":
    main()
