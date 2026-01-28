"""Demo: Reachy Mini emotion expressions.

This template demonstrates the pre-computed emotion library.
Run on robot: /opt/uv/uv run python hello_emotions.py
"""

from reachy_mini import ReachyMini
import time

# Import emotions - in actual use, copy emotions.py to your project
# or import from the snippets location
from emotions import (
    # Static emotions
    happy, sad, curious, neutral, surprised, angry, confused, sleepy, alert,
    # Animated behaviors
    greet, nod, shake_head, think, celebrate, disappointed,
    # Utilities
    play_emotion, emotion_sequence, EMOTIONS,
)


def main():
    with ReachyMini(media_backend="no_media") as mini:
        mini.enable_motors()
        mini.wake_up()
        time.sleep(0.5)

        # =================================================================
        # 1. Static Emotions Demo
        # =================================================================
        print("=== Static Emotions ===")

        print("Happy")
        happy(mini)
        time.sleep(0.5)

        print("Sad")
        sad(mini)
        time.sleep(0.5)

        print("Curious")
        curious(mini)
        time.sleep(0.5)

        print("Surprised (fast!)")
        surprised(mini)
        time.sleep(0.5)

        print("Angry")
        angry(mini)
        time.sleep(0.5)

        print("Confused")
        confused(mini)
        time.sleep(0.5)

        print("Sleepy")
        sleepy(mini)
        time.sleep(0.5)

        print("Alert (snap!)")
        alert(mini)
        time.sleep(0.5)

        print("Neutral (reset)")
        neutral(mini)
        time.sleep(0.5)

        # =================================================================
        # 2. Animated Behaviors Demo
        # =================================================================
        print("\n=== Animated Behaviors ===")

        print("Greet (wave)")
        greet(mini)
        time.sleep(0.3)

        print("Nod (yes)")
        nod(mini)
        time.sleep(0.3)

        print("Shake head (no)")
        shake_head(mini)
        time.sleep(0.3)

        print("Think...")
        think(mini)
        time.sleep(0.3)

        print("Celebrate!")
        celebrate(mini)
        time.sleep(0.3)

        print("Disappointed")
        disappointed(mini)
        time.sleep(0.3)

        neutral(mini)
        time.sleep(0.5)

        # =================================================================
        # 3. Intensity Variations
        # =================================================================
        print("\n=== Intensity Variations (happy) ===")

        print("25% intensity")
        happy(mini, intensity=0.25)
        time.sleep(0.5)

        print("50% intensity")
        happy(mini, intensity=0.5)
        time.sleep(0.5)

        print("100% intensity")
        happy(mini, intensity=1.0)
        time.sleep(0.5)

        neutral(mini)
        time.sleep(0.3)

        # =================================================================
        # 4. Play by Name
        # =================================================================
        print("\n=== Play by Name ===")

        print("Playing 'curious' by name")
        play_emotion(mini, "curious")
        time.sleep(0.5)

        print("Playing 'alert' with custom duration")
        play_emotion(mini, "alert", duration=0.5, intensity=0.8)
        time.sleep(0.5)

        # =================================================================
        # 5. Emotion Sequence
        # =================================================================
        print("\n=== Emotion Sequence ===")

        print("Sequence: curious -> think -> happy")
        emotion_sequence(mini, [curious, think, happy], pause=0.3)
        time.sleep(0.5)

        print("Sequence with intensity variations")
        emotion_sequence(mini, [
            (sad, {"intensity": 0.3}),
            (sad, {"intensity": 0.6}),
            (sad, {"intensity": 1.0}),
        ], pause=0.2)
        time.sleep(0.5)

        # =================================================================
        # 6. Available Emotions
        # =================================================================
        print(f"\n=== Available Emotions ({len(EMOTIONS)} total) ===")
        print(", ".join(sorted(EMOTIONS.keys())))

        # Cleanup
        print("\nGoing to sleep...")
        mini.goto_sleep()


if __name__ == "__main__":
    main()
