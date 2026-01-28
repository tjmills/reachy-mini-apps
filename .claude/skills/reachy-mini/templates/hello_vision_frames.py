import cv2
import time
from reachy_mini import ReachyMini

def main():
    # gstreamer backend required on robot (Wireless)
    with ReachyMini(media_backend="gstreamer") as mini:
        mini.wake_up()
        time.sleep(1.0)  # Camera warmup

        print("Press 'q' to quit")
        while True:
            frame = mini.media.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            cv2.imshow("reachy-mini", frame)
            if (cv2.waitKey(1) & 0xFF) == ord("q"):
                break

        cv2.destroyAllWindows()
        mini.goto_sleep()

if __name__ == "__main__":
    main()
