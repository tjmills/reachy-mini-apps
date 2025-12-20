"""Reachy Mini motion tutorial.

Run this to try several motion patterns and learn the SDK surface:
- Antenna wiggle (basic `goto_target`)
- Head sweep (poses via `create_head_pose`)
- Sinusoidal loops (high-frequency `set_target`)

Tip: For Wireless/LAN robots, set `--localhost-only false` so the client discovers the daemon.
"""

from __future__ import annotations

import argparse
from argparse import BooleanOptionalAction
import time

import numpy as np


def wiggle_antennas(mini) -> None:
    """Basic antenna wiggle using goto_target."""
    mini.goto_target(antennas=[0.5, -0.5], duration=0.6)
    mini.goto_target(antennas=[-0.5, 0.5], duration=0.6)
    mini.goto_target(antennas=[0.0, 0.0], duration=0.4)


def head_sweep(mini, *, create_head_pose) -> None:
    """Sweep head around a few key poses."""
    poses = [
        create_head_pose(z=20, roll=0, pitch=10, degrees=True, mm=True),
        create_head_pose(z=10, roll=20, pitch=-5, degrees=True, mm=True),
        create_head_pose(z=10, roll=-20, pitch=-5, degrees=True, mm=True),
        create_head_pose(z=0, roll=0, pitch=0, degrees=True, mm=True),
    ]
    for pose in poses:
        mini.goto_target(head=pose, duration=1.2, method="minjerk")


def sinusoidal_track(
    mini,
    *,
    total_time: float = 8.0,
    hz: float = 30.0,
    antenna_deg: float = 30.0,
    body_yaw_deg: float = 20.0,
) -> None:
    """Repeated sine-wave motions with `set_target` for smooth continuous control."""
    steps = int(total_time * hz)
    period = total_time
    dt = 1.0 / hz
    for i in range(steps):
        t = i * dt
        phase = 2 * np.pi * (t / period)
        antenna_val = np.deg2rad(antenna_deg) * np.sin(phase * 2)
        body_yaw_val = np.deg2rad(body_yaw_deg) * np.sin(phase)
        mini.set_target(
            antennas=[antenna_val, -antenna_val],
            body_yaw=body_yaw_val,
        )
        time.sleep(dt)


def run_sequence(mini, *, create_head_pose) -> None:
    print("1) Antenna wiggle")
    wiggle_antennas(mini)

    print("2) Head sweep")
    head_sweep(mini, create_head_pose=create_head_pose)

    print("3) Sinusoidal loop (body yaw + antennas)")
    sinusoidal_track(mini)

    print("Done. Robot should have moved through the tutorial sequence.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reachy Mini motion tutorial demo.")
    parser.add_argument(
        "--localhost-only",
        action=BooleanOptionalAction,
        default=False,
        help="Require daemon on localhost (add --no-localhost-only for Wireless/LAN discovery).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Import inside main so the file can be read without deps installed.
    from reachy_mini import ReachyMini  # type: ignore
    from reachy_mini.utils import create_head_pose  # type: ignore

    print(
        f"Connecting to Reachy Mini (localhost_only={args.localhost_only})..."
    )
    with ReachyMini(
        localhost_only=args.localhost_only,
    ) as mini:
        run_sequence(mini, create_head_pose=create_head_pose)


if __name__ == "__main__":
    main()
