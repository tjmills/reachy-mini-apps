from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import numpy as np
import time

def main():
    with ReachyMini(media_backend="no_media") as mini:
        mini.enable_motors()
        mini.wake_up()
        time.sleep(0.3)

        # 1. Antenna wiggle
        print("Wiggling antennas...")
        mini.goto_target(antennas=[0.5, -0.5], duration=0.6)
        mini.goto_target(antennas=[-0.5, 0.5], duration=0.6)
        mini.goto_target(antennas=[0.0, 0.0], duration=0.4)

        # 2. Head sweep through poses
        print("Head sweep...")
        poses = [
            create_head_pose(z=20, roll=0, pitch=10, degrees=True, mm=True),
            create_head_pose(z=10, roll=20, pitch=-5, degrees=True, mm=True),
            create_head_pose(z=10, roll=-20, pitch=-5, degrees=True, mm=True),
            create_head_pose(z=0, roll=0, pitch=0, degrees=True, mm=True),
        ]
        for pose in poses:
            mini.goto_target(pose, duration=1.2, method="minjerk")

        # 3. Sinusoidal body movement (torso yaw + antennas)
        print("Body sway...")
        hz, duration = 30.0, 4.0
        for i in range(int(duration * hz)):
            t = i / hz
            phase = 2 * np.pi * (t / duration)
            antenna = np.deg2rad(30) * np.sin(phase * 2)
            body_yaw = np.deg2rad(20) * np.sin(phase)
            mini.set_target(antennas=(antenna, -antenna), body_yaw=body_yaw)
            time.sleep(1 / hz)

        mini.goto_sleep()

if __name__ == "__main__":
    main()
