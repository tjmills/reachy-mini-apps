"""
Simple example to show takign a frame capture with reachy mini. Must be run on the robot
"""


def main() -> None:

    from reachy_mini import ReachyMini  # type: ignore
    import cv2  # type: ignore

    with ReachyMini(
        media_backend="default"
    ) as mini:
        frame = mini.media.get_frame()
        print(frame)
        cv2.imwrite("./test", frame)


if __name__ == "__main__":
    main()
