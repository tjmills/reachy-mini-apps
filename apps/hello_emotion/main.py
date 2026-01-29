"""
Basic hello emotions app (Wireless).
Run on the robot (SSH/embedded app).

- Loads the pre-programmed emotion moves from:
  pollen-robotics/reachy-mini-emotions-library
- Cycles through a set of emotions:
  plays optional sound + motion for each.
"""

from __future__ import annotations

import argparse
import time
from typing import Iterable, List, Optional


EMOTIONS_DATASET = "pollen-robotics/reachy-mini-emotions-library"


def pick_default_emotions() -> List[str]:
    # These correspond to files present in the dataset (e.g. curious1.json/.wav, welcoming1.json, etc.).
    # You can change this list to any other names in the dataset.
    return [
        "curious1",
        "helpful1",
        "welcoming1",
        "attentive1",
        "attentive2",
        "cheerful1",
        "enthusiastic1",
        "exhausted1",
        "confused1",
        "amazed1",
    ]


def iter_cycle(names: List[str], *, loop_forever: bool) -> Iterable[str]:
    if loop_forever:
        while True:
            for n in names:
                yield n
    else:
        for n in names:
            yield n


def play_emotion(
    mini,
    emotions,
    name: str,
    *,
    play_sound: bool,
    initial_goto_duration: float,
    pause_after: float,
) -> None:
    print(f"→ Emotion: {name}")

    # Play sound first (if present in dataset)
    if play_sound:
        sound = getattr(emotions, "sounds", {}).get(name)
        if sound is not None:
            try:
                mini.media.play_sound(sound)
            except Exception as e:
                print(f"  (sound failed, continuing) {e}")

    # Then play the recorded motion
    move = emotions.get(name)
    mini.play_move(move, initial_goto_duration=initial_goto_duration)

    if pause_after > 0:
        time.sleep(pause_after)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cycle through Reachy Mini emotion moves.")
    parser.add_argument(
        "--emotions",
        type=str,
        default="",
        help="Comma-separated list of emotion names (e.g. curious1,welcoming1,attentive2). "
        "If omitted, uses a default set.",
    )
    parser.add_argument("--no-sound", action="store_true", help="Disable emotion sounds.")
    parser.add_argument("--loop", action="store_true", help="Loop forever (default: one pass).")
    parser.add_argument(
        "--initial-goto",
        type=float,
        default=1.0,
        help="Seconds to smoothly move into the first pose of each recorded move.",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=0.6,
        help="Seconds to pause after each emotion move finishes.",
    )
    args = parser.parse_args()

    # Import inside main so this file is easy to drop into the robot and run.
    from reachy_mini import ReachyMini  # type: ignore
    from reachy_mini.motion.recorded_move import RecordedMoves  # type: ignore

    emotions = RecordedMoves(EMOTIONS_DATASET)

    if args.emotions.strip():
        names = [x.strip() for x in args.emotions.split(",") if x.strip()]
    else:
        names = pick_default_emotions()

    # Filter to only those available in the dataset (so typos don’t crash the script).
    available = set(emotions.list_moves())
    filtered = [n for n in names if n in available]
    if not filtered:
        print("No provided emotions matched the dataset. Falling back to first 10 available moves.")
        filtered = list(emotions.list_moves())[:10]

    print("Connecting to Reachy Mini (on-robot)...")
    with ReachyMini() as mini:
        mini.enable_motors()
        mini.wake_up()
        time.sleep(0.5)

        try:
            for name in iter_cycle(filtered, loop_forever=args.loop):
                play_emotion(
                    mini,
                    emotions,
                    name,
                    play_sound=not args.no_sound,
                    initial_goto_duration=args.initial_goto,
                    pause_after=args.pause,
                )
        finally:
            # leave the robot in a clean state even on Ctrl+C / exceptions
            mini.goto_sleep()


if __name__ == "__main__":
    main()
