"""
Simple example to show takign a frame capture with reachy mini. Must be run on the robot
"""
import time

def main() -> None:

    from reachy_mini import ReachyMini  # type: ignore
    import cv2  # type: ignore

    with ReachyMini(
        media_backend="default"
    ) as mini:
        mini.wake_up()
        time.sleep(1)
        frame = mini.media.get_frame()
        cv2.imwrite("./test.png", frame)
        mini.goto_sleep()


if __name__ == "__main__":
    main()
