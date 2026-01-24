"""Dog tracking app for Reachy Mini using remote HuggingFace inference."""

from __future__ import annotations

import asyncio
import signal
import time


async def main() -> None:
    """Main entry point for dog tracker."""
    # Import inside main so file can be read without deps
    from reachy_mini import ReachyMini  # type: ignore

    from config import Config
    from controller import Controller
    from detector import Detector

    # Load configuration
    config = Config.from_env()
    print("Dog Tracker starting...")
    print(f"  Model: {config.model}")
    print(f"  Target: {config.target_label} (conf >= {config.confidence_threshold})")
    print(f"  Detection rate: {config.detection_hz} Hz")
    print(f"  Control rate: {config.control_hz} Hz")

    # Graceful shutdown handling
    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        print("\nShutdown requested...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    with ReachyMini(media_backend="default") as mini:
        print("Connected to Reachy Mini")
        mini.wake_up()
        time.sleep(0.5)

        # Get frame dimensions from first capture
        frame = mini.media.get_frame()
        if frame is None:
            print("ERROR: Could not capture frame from camera")
            return
        frame_height, frame_width = frame.shape[:2]
        print(f"Camera resolution: {frame_width}x{frame_height}")

        # Initialize components
        detector = Detector(config)
        controller = Controller(config, frame_width, frame_height)

        # Timing
        control_interval = 1.0 / config.control_hz
        detection_interval = 1.0 / config.detection_hz
        last_detection_submit = 0.0

        print("Tracking loop started. Press Ctrl+C to stop.")

        try:
            while not shutdown_event.is_set():
                loop_start = time.monotonic()

                # Capture frame
                frame = mini.media.get_frame()
                if frame is None:
                    await asyncio.sleep(0.01)
                    continue

                # Submit frame for detection at detection rate
                now = time.monotonic()
                if now - last_detection_submit >= detection_interval:
                    detector.submit_frame(frame)
                    last_detection_submit = now

                # Get latest detection result
                detection, age = detector.get_detection()

                # Compute motion command
                yaw, pitch, body_yaw = controller.update(detection, age)

                # Apply to robot (using set_target for smooth continuous control)
                # Note: Reachy Mini head uses roll (z-rotation), pitch (x), yaw (y) convention
                # For simplicity, we map our yaw to body_yaw and use head pitch
                mini.set_target(
                    body_yaw=yaw,  # Use body yaw for horizontal tracking (larger range)
                    head={"pitch": pitch},  # Head pitch for vertical tracking
                )

                # Allow async tasks to run
                await asyncio.sleep(0)

                # Maintain control loop rate
                elapsed = time.monotonic() - loop_start
                sleep_time = control_interval - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        finally:
            print("Returning to neutral position...")
            mini.goto_target(body_yaw=0.0, head={"pitch": 0.0}, duration=1.0)
            time.sleep(1.0)
            mini.goto_sleep()
            print("Dog Tracker stopped.")


if __name__ == "__main__":
    asyncio.run(main())
