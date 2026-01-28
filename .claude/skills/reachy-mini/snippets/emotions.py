"""Pre-computed emotion expressions for Reachy Mini.

Emotions are expressed through motion patterns using:
- Antennas (primary indicator) - range roughly ±1.0 radians
- Head pose (roll, pitch, z height)
- Body rotation (yaw)

All functions accept:
- mini: ReachyMini instance
- duration: seconds for the motion (default varies by emotion)
- intensity: 0.0-1.0 scaling factor (default 1.0)
"""

import numpy as np
import time
from reachy_mini.utils import create_head_pose


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _scale(value, intensity):
    """Scale a value by intensity factor."""
    return value * intensity


# =============================================================================
# Static Emotions (single pose)
# =============================================================================

def happy(mini, duration=0.8, intensity=1.0):
    """Express happiness - antennas up, head slightly up and tilted."""
    ant = _scale(0.6, intensity)
    pitch = _scale(8, intensity)
    roll = _scale(5, intensity)
    z = _scale(15, intensity)

    pose = create_head_pose(z=z, roll=roll, pitch=pitch, degrees=True, mm=True)
    mini.goto_target(pose, antennas=[ant, ant], duration=duration, method="minjerk")


def sad(mini, duration=1.2, intensity=1.0):
    """Express sadness - antennas drooped down, head lowered."""
    ant = _scale(-0.7, intensity)
    pitch = _scale(-15, intensity)
    z = _scale(-10, intensity)

    pose = create_head_pose(z=z, roll=0, pitch=pitch, degrees=True, mm=True)
    mini.goto_target(pose, antennas=[ant, ant], duration=duration, method="minjerk")


def curious(mini, duration=0.7, intensity=1.0):
    """Express curiosity - asymmetric antennas, head tilt."""
    ant_l = _scale(0.4, intensity)
    ant_r = _scale(-0.2, intensity)
    roll = _scale(15, intensity)
    pitch = _scale(5, intensity)
    z = _scale(10, intensity)

    pose = create_head_pose(z=z, roll=roll, pitch=pitch, degrees=True, mm=True)
    mini.goto_target(pose, antennas=[ant_l, ant_r], duration=duration, method="minjerk")


def neutral(mini, duration=0.6, intensity=1.0):
    """Reset to neutral centered position."""
    pose = create_head_pose(z=0, roll=0, pitch=0, degrees=True, mm=True)
    mini.goto_target(pose, antennas=[0.0, 0.0], body_yaw=0.0, duration=duration, method="minjerk")


def surprised(mini, duration=0.3, intensity=1.0):
    """Express surprise - sharp antennas up, head back quickly."""
    ant = _scale(0.8, intensity)
    pitch = _scale(12, intensity)
    z = _scale(20, intensity)

    pose = create_head_pose(z=z, roll=0, pitch=pitch, degrees=True, mm=True)
    mini.goto_target(pose, antennas=[ant, ant], duration=duration, method="cartoon")


def angry(mini, duration=0.5, intensity=1.0):
    """Express anger - antennas forward/down, head thrust forward."""
    ant = _scale(-0.5, intensity)
    pitch = _scale(-8, intensity)
    z = _scale(5, intensity)

    pose = create_head_pose(z=z, roll=0, pitch=pitch, degrees=True, mm=True)
    mini.goto_target(pose, antennas=[ant, ant], duration=duration, method="cartoon")


def confused(mini, duration=0.8, intensity=1.0):
    """Express confusion - asymmetric antennas (opposite of curious), slight tilt."""
    ant_l = _scale(-0.3, intensity)
    ant_r = _scale(0.5, intensity)
    roll = _scale(-12, intensity)
    pitch = _scale(3, intensity)

    pose = create_head_pose(z=0, roll=roll, pitch=pitch, degrees=True, mm=True)
    mini.goto_target(pose, antennas=[ant_l, ant_r], duration=duration, method="minjerk")


def sleepy(mini, duration=1.5, intensity=1.0):
    """Express sleepiness - drooping antennas, head nodding down slowly."""
    ant = _scale(-0.6, intensity)
    pitch = _scale(-20, intensity)
    z = _scale(-15, intensity)

    pose = create_head_pose(z=z, roll=0, pitch=pitch, degrees=True, mm=True)
    mini.goto_target(pose, antennas=[ant, ant], duration=duration, method="minjerk")


def alert(mini, duration=0.25, intensity=1.0):
    """Express alertness - quick snap to attention."""
    ant = _scale(0.5, intensity)
    pitch = _scale(5, intensity)
    z = _scale(18, intensity)

    pose = create_head_pose(z=z, roll=0, pitch=pitch, degrees=True, mm=True)
    mini.goto_target(pose, antennas=[ant, ant], duration=duration, method="cartoon")


# =============================================================================
# Animated Behaviors (sequences)
# =============================================================================

def greet(mini, duration=2.0, intensity=1.0):
    """Greeting - wave antennas with a friendly nod."""
    step = duration / 5
    ant_up = _scale(0.6, intensity)
    ant_wave = _scale(0.4, intensity)
    pitch_nod = _scale(10, intensity)

    # Start happy
    pose_up = create_head_pose(z=10, roll=0, pitch=pitch_nod, degrees=True, mm=True)
    mini.goto_target(pose_up, antennas=[ant_up, ant_up], duration=step, method="minjerk")

    # Wave antennas
    mini.goto_target(antennas=[ant_up, ant_wave], duration=step * 0.7)
    mini.goto_target(antennas=[ant_wave, ant_up], duration=step * 0.7)
    mini.goto_target(antennas=[ant_up, ant_wave], duration=step * 0.7)

    # Settle
    pose_settle = create_head_pose(z=5, roll=0, pitch=5, degrees=True, mm=True)
    mini.goto_target(pose_settle, antennas=[ant_wave, ant_wave], duration=step, method="minjerk")


def nod(mini, duration=1.0, intensity=1.0):
    """Agreement nod - head moves up then down."""
    step = duration / 3
    pitch_up = _scale(10, intensity)
    pitch_down = _scale(-8, intensity)

    pose_up = create_head_pose(z=5, roll=0, pitch=pitch_up, degrees=True, mm=True)
    pose_down = create_head_pose(z=-5, roll=0, pitch=pitch_down, degrees=True, mm=True)
    pose_center = create_head_pose(z=0, roll=0, pitch=0, degrees=True, mm=True)

    mini.goto_target(pose_up, duration=step, method="minjerk")
    mini.goto_target(pose_down, duration=step, method="minjerk")
    mini.goto_target(pose_center, duration=step, method="minjerk")


def shake_head(mini, duration=1.2, intensity=1.0):
    """Disagreement - side-to-side head shake."""
    step = duration / 4
    roll_amt = _scale(18, intensity)

    pose_left = create_head_pose(z=0, roll=roll_amt, pitch=0, degrees=True, mm=True)
    pose_right = create_head_pose(z=0, roll=-roll_amt, pitch=0, degrees=True, mm=True)
    pose_center = create_head_pose(z=0, roll=0, pitch=0, degrees=True, mm=True)

    mini.goto_target(pose_left, duration=step, method="minjerk")
    mini.goto_target(pose_right, duration=step, method="minjerk")
    mini.goto_target(pose_left, duration=step, method="minjerk")
    mini.goto_target(pose_center, duration=step, method="minjerk")


def think(mini, duration=2.0, intensity=1.0):
    """Thinking pose - tilt head and hold."""
    hold_time = duration * 0.7
    transition = duration * 0.15

    roll = _scale(20, intensity)
    pitch = _scale(8, intensity)
    ant_l = _scale(0.2, intensity)
    ant_r = _scale(-0.4, intensity)

    pose = create_head_pose(z=5, roll=roll, pitch=pitch, degrees=True, mm=True)
    mini.goto_target(pose, antennas=[ant_l, ant_r], duration=transition, method="minjerk")
    time.sleep(hold_time)

    # Return to neutral
    pose_neutral = create_head_pose(z=0, roll=0, pitch=0, degrees=True, mm=True)
    mini.goto_target(pose_neutral, antennas=[0.0, 0.0], duration=transition, method="minjerk")


def celebrate(mini, duration=2.5, intensity=1.0):
    """Celebration - excited wiggle with body sway."""
    hz = 30.0
    frames = int(duration * hz)

    ant_amp = _scale(0.5, intensity)
    yaw_amp = np.deg2rad(_scale(15, intensity))

    for i in range(frames):
        t = i / hz
        phase = 2 * np.pi * (t / (duration / 3))

        antenna_l = ant_amp * np.sin(phase * 2) + _scale(0.3, intensity)
        antenna_r = ant_amp * np.sin(phase * 2 + np.pi) + _scale(0.3, intensity)
        body_yaw = yaw_amp * np.sin(phase)

        mini.set_target(antennas=(antenna_l, antenna_r), body_yaw=body_yaw)
        time.sleep(1 / hz)

    # Settle happy
    mini.goto_target(antennas=[0.4, 0.4], body_yaw=0.0, duration=0.3)


def disappointed(mini, duration=2.0, intensity=1.0):
    """Disappointment - deflate from hopeful to sad."""
    step = duration / 3

    # Start hopeful (antennas up)
    ant_up = _scale(0.5, intensity)
    pitch_up = _scale(10, intensity)
    pose_hope = create_head_pose(z=10, roll=0, pitch=pitch_up, degrees=True, mm=True)
    mini.goto_target(pose_hope, antennas=[ant_up, ant_up], duration=step * 0.5, method="minjerk")

    time.sleep(step * 0.3)

    # Deflate slowly
    ant_down = _scale(-0.6, intensity)
    pitch_down = _scale(-12, intensity)
    pose_sad = create_head_pose(z=-10, roll=0, pitch=pitch_down, degrees=True, mm=True)
    mini.goto_target(pose_sad, antennas=[ant_down, ant_down], duration=step * 1.5, method="minjerk")


# =============================================================================
# Utilities
# =============================================================================

EMOTIONS = {
    # Static
    "happy": happy,
    "sad": sad,
    "curious": curious,
    "neutral": neutral,
    "surprised": surprised,
    "angry": angry,
    "confused": confused,
    "sleepy": sleepy,
    "alert": alert,
    # Animated
    "greet": greet,
    "nod": nod,
    "shake_head": shake_head,
    "think": think,
    "celebrate": celebrate,
    "disappointed": disappointed,
}


def play_emotion(mini, name, **kwargs):
    """Play an emotion by string name.

    Args:
        mini: ReachyMini instance
        name: emotion name (e.g., "happy", "greet")
        **kwargs: passed to emotion function (duration, intensity)

    Raises:
        ValueError: if emotion name not found
    """
    if name not in EMOTIONS:
        raise ValueError(f"Unknown emotion: {name}. Available: {list(EMOTIONS.keys())}")
    EMOTIONS[name](mini, **kwargs)


def emotion_sequence(mini, emotions, pause=0.3):
    """Play a sequence of emotions with pauses between.

    Args:
        mini: ReachyMini instance
        emotions: list of emotion functions or (function, kwargs) tuples
        pause: seconds to pause between emotions

    Example:
        emotion_sequence(mini, [happy, sad, curious])
        emotion_sequence(mini, [(happy, {"intensity": 0.5}), sad])
    """
    for i, item in enumerate(emotions):
        if isinstance(item, tuple):
            func, kwargs = item
            func(mini, **kwargs)
        else:
            item(mini)

        if i < len(emotions) - 1:
            time.sleep(pause)
