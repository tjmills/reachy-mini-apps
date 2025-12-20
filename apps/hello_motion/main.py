"""Minimal motion example for Reachy Mini.

This intentionally stays conservative and may need adjustment depending on your device mode
(Wireless / Lite / Simulation) and your daemon connection settings.
"""

from __future__ import annotations

def main() -> None:
    # Import is expected to work after `uv sync`
    from reachy_mini import ReachyMini  # type: ignore
    from reachy_mini.utils import create_head_pose  # type: ignore

    # Many SDKs support a context manager for clean connect/disconnect.
    # If ReachyMini(...) requires host/port, pass it here.
    with ReachyMini(localhost_only=False) as mini:
        mini.goto_target(
            head=create_head_pose(z=10, roll=10, degrees=True, mm=True),
            duration=3.0,
        )
        mini.goto_target(
            head=create_head_pose(z=10, roll=-10, degrees=True, mm=True),
            duration=3.0,
        )
        print("Sent motion command (check robot/sim).")

if __name__ == "__main__":
    main()
