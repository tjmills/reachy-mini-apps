"""Reachy Mini dance party.

This script choreographs a short dance with coordinated body yaw, head waves,
antenna flicks, and matching sound cues.

Examples:
- Wireless/LAN robot: `uv run python apps/dance_party/main.py --no-localhost-only`
- Local daemon (Lite/Sim): `uv run python apps/dance_party/main.py --localhost-only`
"""

from __future__ import annotations

import argparse
from argparse import BooleanOptionalAction
import time

import numpy as np


def safe_play_sound(mini, sound_file: str) -> None:
    """Try to play a bundled sound; skip gracefully if missing."""
    try:
        mini.media.play_sound(sound_file)
    except Exception as exc:  # pragma: no cover - best-effort helper
        print(f"[audio skipped] {sound_file}: {exc}")


def antenna_groove(mini, repeats: int = 4, amp_rad: float = np.deg2rad(60)) -> None:
    """Rhythmic antenna flicks."""
    pattern = [
        [amp_rad, -amp_rad],
        [-amp_rad, amp_rad],
    ]
    for _ in range(repeats):
        for antennas in pattern:
            mini.goto_target(antennas=antennas, duration=0.4, method="minjerk")
    mini.goto_target(antennas=[0.0, 0.0], duration=0.4)


def body_sway(mini, *, swings: int = 3, yaw_deg: float = 30) -> None:
    """Slow body yaw sways."""
    yaw_rad = np.deg2rad(yaw_deg)
    for i in range(swings):
        direction = 1 if i % 2 == 0 else -1
        mini.goto_target(body_yaw=direction * yaw_rad, duration=0.8, method="minjerk")
    mini.goto_target(body_yaw=0.0, duration=0.6, method="minjerk")


def head_wave(
    mini,
    *,
    create_head_pose,
    duration: float = 8.0,
    hz: float = 30.0,
    roll_deg: float = 15.0,
    pitch_deg: float = 12.0,
    z_mm: float = 20.0,
) -> None:
    """Continuous head wave using set_target for smooth curves."""
    steps = int(duration * hz)
    dt = 1.0 / hz
    for i in range(steps):
        t = i * dt
        roll = roll_deg * np.sin(2 * np.pi * t / 2.2)  # quicker roll
        pitch = pitch_deg * np.sin(2 * np.pi * t / 3.1)  # slower nod
        z = z_mm + 5 * np.sin(2 * np.pi * t / 4.0)
        pose = create_head_pose(z=z, roll=roll, pitch=pitch, mm=True, degrees=True)
        mini.set_target(head=pose)
        time.sleep(dt)


def dance(mini, *, create_head_pose) -> None:
    print("Dance intro: wake-up chime + antenna groove")
    safe_play_sound(mini, "wake_up.wav")
    antenna_groove(mini)

    print("Body sway with beat")
    safe_play_sound(mini, "impatient1.wav")
    body_sway(mini)

    print("Head wave freestyle")
    head_wave(mini, create_head_pose=create_head_pose)

    print("Final pose + outro chime")
    mini.goto_target(
        head=create_head_pose(z=10, roll=0, pitch=-5, degrees=True, mm=True),
        antennas=[0.2, 0.2],
        body_yaw=0.0,
        duration=1.0,
    )
    safe_play_sound(mini, "go_sleep.wav")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reachy Mini dance party.")
    parser.add_argument(
        "--localhost-only",
        action=BooleanOptionalAction,
        default=False,
        help="Require daemon on localhost (add --no-localhost-only for Wireless/LAN discovery).",
    )
    parser.add_argument(
        "--media-backend",
        type=str,
        default="default",
        help="Media backend: default|no_media|default_no_video|gstreamer|webrtc",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Lazy import so file can be read without deps installed.
    from reachy_mini import ReachyMini  # type: ignore
    from reachy_mini.utils import create_head_pose  # type: ignore

    print(
        f"Connecting to Reachy Mini (localhost_only={args.localhost_only}, media_backend={args.media_backend})..."
    )
    with ReachyMini(
        localhost_only=args.localhost_only,
        media_backend=args.media_backend,
    ) as mini:
        dance(mini, create_head_pose=create_head_pose)


if __name__ == "__main__":
    main()
