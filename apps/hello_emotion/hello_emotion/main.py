"""Play recorded Reachy Mini emotions with optional synchronized audio."""

from __future__ import annotations

import argparse
import logging
import threading
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from reachy_mini import ReachyMini, ReachyMiniApp
from reachy_mini.motion.recorded_move import RecordedMoves
from reachy_mini.reachy_mini import INIT_ANTENNAS_JOINT_POSITIONS, INIT_HEAD_POSE

LOGGER = logging.getLogger(__name__)
EMOTIONS_DATASET = "pollen-robotics/reachy-mini-emotions-library"
DEFAULT_EMOTIONS = (
    "curious1",
    "helpful1",
    "welcoming1",
    "attentive1",
    "cheerful1",
    "enthusiastic1",
)


@dataclass(frozen=True)
class EmotionConfig:
    """Runtime options for the emotion player."""

    names: tuple[str, ...] = DEFAULT_EMOTIONS
    play_sound: bool = True
    loop: bool = False
    initial_goto_duration: float = 1.0
    pause_after: float = 0.6

    def __post_init__(self) -> None:
        if self.initial_goto_duration < 0:
            raise ValueError("initial_goto_duration cannot be negative")
        if self.pause_after < 0:
            raise ValueError("pause_after cannot be negative")


def parse_names(value: str) -> tuple[str, ...]:
    """Parse a comma-separated move list."""
    return tuple(name.strip() for name in value.split(",") if name.strip())


def select_moves(requested: Sequence[str], available: Sequence[str]) -> tuple[str, ...]:
    """Return requested moves that exist, preserving request order."""
    available_set = set(available)
    selected = tuple(name for name in requested if name in available_set)
    if not selected:
        raise ValueError("None of the requested emotions are available")
    return selected


def emotion_sequence(names: Sequence[str], loop: bool) -> Iterable[str]:
    """Yield a finite sequence or repeat it until the caller stops."""
    if not loop:
        yield from names
        return

    while True:
        yield from names


def return_to_neutral(mini: ReachyMini, duration: float = 1.0) -> None:
    """Return the robot to a predictable pose without playing sleep audio."""
    mini.goto_target(
        head=INIT_HEAD_POSE,
        antennas=INIT_ANTENNAS_JOINT_POSITIONS,
        body_yaw=0.0,
        duration=duration,
        method="minjerk",
    )


class HelloEmotion(ReachyMiniApp):
    """Canonical recorded-emotion player."""

    custom_app_url = None
    dont_start_webserver = True
    request_media_backend = "default"

    def __init__(self, config: EmotionConfig | None = None) -> None:
        super().__init__()
        self.config = config or EmotionConfig()

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event) -> None:
        """Play the configured emotion sequence."""
        library = RecordedMoves(EMOTIONS_DATASET)
        available = library.list_moves()
        selected = select_moves(self.config.names, available)
        missing = [name for name in self.config.names if name not in set(available)]
        if missing:
            LOGGER.warning("Skipping unavailable moves: %s", ", ".join(missing))

        reachy_mini.enable_motors()
        try:
            for name in emotion_sequence(selected, self.config.loop):
                if stop_event.is_set():
                    break
                LOGGER.info("Playing emotion: %s", name)
                reachy_mini.play_move(
                    library.get(name),
                    initial_goto_duration=self.config.initial_goto_duration,
                    sound=self.config.play_sound,
                )
                if stop_event.wait(self.config.pause_after):
                    break
        finally:
            reachy_mini.cancel_move()
            return_to_neutral(reachy_mini)


def parse_args() -> argparse.Namespace:
    """Parse direct-run options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--emotions",
        default=",".join(DEFAULT_EMOTIONS),
        help="Comma-separated recorded move names.",
    )
    parser.add_argument("--no-sound", action="store_true")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--initial-goto", type=float, default=1.0)
    parser.add_argument("--pause", type=float, default=0.6)
    parser.add_argument("--list", action="store_true", help="List moves and exit.")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    """Run the app outside the dashboard."""
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.list:
        for name in sorted(RecordedMoves(EMOTIONS_DATASET).list_moves()):
            print(name)
        return

    names = parse_names(args.emotions)
    if not names:
        raise SystemExit("--emotions must contain at least one move name")

    app = HelloEmotion(
        EmotionConfig(
            names=names,
            play_sound=not args.no_sound,
            loop=args.loop,
            initial_goto_duration=args.initial_goto,
            pause_after=args.pause,
        )
    )
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()


if __name__ == "__main__":
    main()
