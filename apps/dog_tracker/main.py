"""Dog tracker app for Reachy Mini using remote HuggingFace inference.

Scans the room and reacts with a recorded emotion when target detected.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np


@dataclass
class Box:
    """Bounding box from detection."""
    xmin: float
    ymin: float
    xmax: float
    ymax: float


@dataclass
class DetResult:
    """Detection result matching InferenceClient format."""
    label: str
    score: float
    box: Box


def run_endpoint_detection(
    endpoint_url: str,
    token: str,
    jpeg_bytes: bytes,
    max_retries: int = 12,
    initial_wait: float = 5.0,
) -> list[DetResult]:
    """Run object detection on a dedicated HF endpoint.

    Retries on 503 (endpoint scaling up from zero) with exponential backoff,
    capped at 30s between attempts. Default 12 retries ≈ ~3 min total wait.
    """
    import requests

    wait = initial_wait
    for attempt in range(max_retries + 1):
        resp = requests.post(
            endpoint_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "image/jpeg",
            },
            data=jpeg_bytes,
        )
        if resp.status_code != 503 or attempt == max_retries:
            resp.raise_for_status()
            break
        print(f"  Endpoint waking up... retry {attempt + 1}/{max_retries} in {wait:.0f}s")
        time.sleep(wait)
        wait = min(wait * 1.5, 30.0)

    raw_results = resp.json()
    return [
        DetResult(
            label=r["label"],
            score=r["score"],
            box=Box(**r["box"]),
        )
        for r in raw_results
    ]


def test_hf_connection(config) -> bool:
    """Test HuggingFace API connection (Phase 1)."""
    from huggingface_hub import HfApi

    try:
        print("Testing HuggingFace API connection...")
        api = HfApi(token=config.hf_token)
        # Verify token by getting user info
        user_info = api.whoami()
        print(f"HF API connection successful!")
        print(f"  Authenticated as: {user_info.get('name', user_info.get('id', 'unknown'))}")
        # Verify model exists
        model_info = api.model_info(config.model)
        print(f"  Model verified: {model_info.id}")
        return True
    except Exception as e:
        print(f"HF API connection FAILED: {e}")
        return False


def main() -> None:
    """Main entry point for dog tracker."""
    # Import inside main so file can be read without deps
    from reachy_mini import ReachyMini  # type: ignore
    import cv2  # type: ignore

    from config import Config

    # Load configuration
    config = Config.from_env()
    print("Dog Tracker starting...")
    print(f"  Model: {config.model}")
    print(f"  Target: {config.target_label} (conf >= {config.confidence_threshold})")

    # Phase 1: Test HF API connection
    if not test_hf_connection(config):
        print("Aborting: Cannot connect to HuggingFace API")
        return

    # Force correct on-robot media backend
    with ReachyMini(media_backend="gstreamer") as mini:
        # Enable motors FIRST, then wake up
        mini.enable_motors()
        mini.wake_up()
        time.sleep(1.0)  # let the motion finish + camera settle
        print("Connected to Reachy Mini (motors enabled)")
        time.sleep(1)

        # Test frame capture like hello_vision (with retries for camera init)
        frame = None
        for attempt in range(5):
            frame = mini.media.get_frame()
            if frame is not None:
                break
            print(f"Waiting for camera... (attempt {attempt + 1}/5)")
            time.sleep(0.5)

        if frame is None:
            print("ERROR: Could not capture frame from camera")
            mini.goto_sleep()
            return

        frame_height, frame_width = frame.shape[:2]
        print(f"Camera resolution: {frame_width}x{frame_height}")
        cv2.imwrite("./test_frame.png", frame)
        print("Saved test_frame.png")

        # Phase 2: Test object detection on captured frame
        from huggingface_hub import InferenceClient

        print("\nTesting object detection...")
        if config.endpoint_url:
            client = InferenceClient(model=config.endpoint_url, token=config.hf_token)
            print(f"  Using dedicated endpoint: {config.endpoint_url}")
        else:
            client = InferenceClient(provider="hf-inference", token=config.hf_token)
            print("  Using HF Serverless API")
        # Encode frame as JPEG
        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not success:
            print("ERROR: Failed to encode frame as JPEG")
            mini.goto_sleep()
            return
        jpeg_bytes = buffer.tobytes()
        print(f"  Encoded frame: {len(jpeg_bytes)} bytes")

        # Run detection
        try:
            if config.endpoint_url:
                results = run_endpoint_detection(
                    config.endpoint_url, config.hf_token, jpeg_bytes
                )
            else:
                results = client.object_detection(
                    jpeg_bytes,
                    model=config.model,
                    threshold=config.confidence_threshold,
                )
            print(f"  Raw API results: {len(results)} objects detected")
            for i, r in enumerate(results[:5]):  # Show first 5
                print(f"    [{i}] label={r.label}, score={r.score:.2f}, box={r.box}")
        except Exception as e:
            print(f"ERROR: Object detection failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            mini.goto_sleep()
            return

        # Filter for target
        from detector import Detection
        detection = None
        for result in results:
            if result.label is None:
                continue
            if (result.label.lower() == config.target_label.lower()
                    and result.score >= config.confidence_threshold):
                box = result.box
                detection = Detection(
                    label=result.label,
                    score=result.score,
                    box=(int(box.xmin), int(box.ymin), int(box.xmax), int(box.ymax)),
                )
                break  # Take first match

        if detection is None:
            print(f"No '{config.target_label}' detected in frame")
        else:
            print(f"Detection successful!")
            print(f"  Label: {detection.label}")
            print(f"  Confidence: {detection.score:.2f}")
            print(f"  Bounding box: {detection.box}")
            print(f"  Center: {detection.center}")

            # Draw bounding box on frame and save
            # Make frame writable (OpenCV may return readonly array)
            frame = frame.copy()
            x_min, y_min, x_max, y_max = detection.box
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            label_text = f"{detection.label}: {detection.score:.2f}"
            cv2.putText(frame, label_text, (x_min, y_min - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.imwrite("./test_frame_annotated.png", frame)
            print("Saved test_frame_annotated.png with bounding box")

        # Continuous scan + react loop
        from controller import Controller
        from reachy_mini.motion.recorded_move import RecordedMoves  # type: ignore
        from reachy_mini.utils import create_head_pose  # type: ignore

        EMOTIONS_DATASET = "pollen-robotics/reachy-mini-emotions-library"
        print(f"\nLoading emotions from {EMOTIONS_DATASET}...")
        emotions = RecordedMoves(EMOTIONS_DATASET)

        available = emotions.list_moves()
        if config.reaction_emotion not in available:
            print(f"ERROR: Emotion '{config.reaction_emotion}' not found in dataset.")
            print(f"  Available: {', '.join(sorted(available))}")
            mini.goto_sleep()
            return

        print(f"\n=== Scanning for '{config.target_label}' (Ctrl+C to stop) ===")
        print(f"  Reaction: {config.reaction_emotion} emotion")
        print(f"  Scan-only after reaction: {config.scan_only_duration}s")

        controller = Controller(config, frame_width, frame_height)

        last_inference_time = 0.0
        last_good_frame_time = 0.0
        last_status_time = time.monotonic()
        last_reaction_time = 0.0
        detection_paused = False  # True during scan-only window
        current_detection = None
        detection_interval = 1.0 / config.detection_hz

        # Stale detection threshold
        max_detection_age = 3.0  # seconds

        try:
            while True:
                loop_start = time.monotonic()

                # Check if scan-only window has expired
                if detection_paused:
                    if (loop_start - last_reaction_time) >= config.scan_only_duration:
                        detection_paused = False
                        print(f"  Scan-only window ended, resuming detection")

                # Only run inference when not in scan-only window
                if not detection_paused and loop_start - last_inference_time >= detection_interval:
                    frame = mini.media.get_frame()
                    if frame is not None:
                        frame_capture_time = time.monotonic()

                        # Resize frame to reduce latency
                        h, w = frame.shape[:2]
                        scale = 320 / w
                        small_frame = cv2.resize(frame, (320, int(h * scale)))
                        success, buffer = cv2.imencode(
                            ".jpg", small_frame, [cv2.IMWRITE_JPEG_QUALITY, 65]
                        )
                        if success:
                            jpeg_bytes = buffer.tobytes()
                            try:
                                inference_start = time.monotonic()
                                if config.endpoint_url:
                                    results = run_endpoint_detection(
                                        config.endpoint_url, config.hf_token, jpeg_bytes
                                    )
                                else:
                                    results = client.object_detection(
                                        jpeg_bytes,
                                        model=config.model,
                                        threshold=config.confidence_threshold,
                                    )
                                receipt_time = time.monotonic()
                                age_at_receipt = receipt_time - frame_capture_time

                                if age_at_receipt > max_detection_age:
                                    pass  # Discard stale results
                                else:
                                    found_detection = None
                                    for r in results:
                                        if r.label and r.label.lower() == config.target_label.lower():
                                            box = r.box
                                            found_detection = Detection(
                                                label=r.label,
                                                score=r.score,
                                                box=(
                                                    int(box.xmin / scale),
                                                    int(box.ymin / scale),
                                                    int(box.xmax / scale),
                                                    int(box.ymax / scale),
                                                ),
                                            )
                                            break

                                    if found_detection is not None:
                                        current_detection = found_detection
                                        last_good_frame_time = frame_capture_time
                                    else:
                                        current_detection = None
                            except Exception as e:
                                print(f"  Detection error: {e}")
                    last_inference_time = loop_start

                # Compute detection age
                detection_age = (
                    (loop_start - last_good_frame_time)
                    if last_good_frame_time > 0
                    else 999.0
                )

                # Update controller
                yaw, pitch, body_yaw, reaction_triggered = controller.update(
                    current_detection, detection_age
                )

                # React on detection
                if reaction_triggered:
                    last_reaction_time = loop_start
                    print(f"  Reacting: {config.reaction_emotion}!")
                    sound = emotions.sounds.get(config.reaction_emotion)
                    if sound is not None:
                        try:
                            mini.media.play_sound(sound)
                        except Exception as e:
                            print(f"  (sound failed, continuing) {e}")
                    move = emotions.get(config.reaction_emotion)
                    mini.play_move(move, initial_goto_duration=1.0)
                    controller.resume_scanning()
                    detection_paused = True
                    current_detection = None
                    last_good_frame_time = 0.0
                    print(f"  Scanning only for {config.scan_only_duration}s...")
                    continue

                # Apply scanning motion via set_target
                head_pose = create_head_pose(yaw=yaw, pitch=pitch, degrees=False)
                mini.set_target(head=head_pose, body_yaw=body_yaw)

                # Status every 3 seconds
                if loop_start - last_status_time >= 3.0:
                    print(
                        f"  Mode: {controller.mode.value}, "
                        f"Yaw: {np.rad2deg(yaw):.1f}, "
                        f"Pitch: {np.rad2deg(pitch):.1f}, "
                        f"Body: {np.rad2deg(body_yaw):.1f}"
                    )
                    last_status_time = loop_start

                # Sleep to maintain control rate
                elapsed = time.monotonic() - loop_start
                sleep_time = max(0, (1.0 / config.control_hz) - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n\nStopping tracker (Ctrl+C received)...")

        mini.goto_sleep()
        print("Dog Tracker stopped.")


if __name__ == "__main__":
    main()
