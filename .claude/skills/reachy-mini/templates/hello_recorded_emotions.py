"""Demo: Pre-recorded emotions from HuggingFace dataset.

Loads emotion trajectories + sounds from the pollen-robotics/reachy-mini-emotions-library
dataset using RecordedMoves. Each emotion has a motion trajectory (.json) and an optional
sound file (.wav).

Run on robot: /opt/uv/uv run python hello_recorded_emotions.py
Requires: media_backend="default" (sound playback needs audio support)
"""

import time

from reachy_mini import ReachyMini
from reachy_mini.motion.recorded_move import RecordedMoves

EMOTIONS_DATASET = "pollen-robotics/reachy-mini-emotions-library"


def main():
    # Load all emotion moves from the HuggingFace dataset
    emotions = RecordedMoves(EMOTIONS_DATASET)

    # Show what's available
    available = emotions.list_moves()
    print(f"Available emotions ({len(available)}): {', '.join(sorted(available))}")

    # Pick a few to demo
    demo_emotions = ["curious1", "welcoming1", "cheerful1", "confused1", "amazed1"]
    demo_emotions = [e for e in demo_emotions if e in available]

    # media_backend="default" needed for sound playback on robot
    with ReachyMini(media_backend="default") as mini:
        mini.enable_motors()
        mini.wake_up()
        time.sleep(0.5)

        try:
            for name in demo_emotions:
                print(f"Playing: {name}")

                # Play the optional sound (if this emotion has a .wav)
                sound = emotions.sounds.get(name)
                if sound is not None:
                    mini.media.play_sound(sound)

                # Play the recorded motion trajectory
                move = emotions.get(name)
                mini.play_move(move, initial_goto_duration=1.0)

                time.sleep(0.6)
        finally:
            mini.goto_sleep()


if __name__ == "__main__":
    main()
