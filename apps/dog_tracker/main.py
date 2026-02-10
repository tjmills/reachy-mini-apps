"""Dog tracker app for Reachy Mini using remote HuggingFace inference.

Scans the room and reacts with a recorded emotion when target detected.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass

import numpy as np

# Center-crop dimensions (applied to 320px-wide resized frame)
CENTER_CROP_WIDTH = 240   # pixels
CENTER_CROP_HEIGHT = 180  # pixels
NUM_PLAYS=3

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
        # Resize and center-crop for detection
        h, w = frame.shape[:2]
        test_scale = 320 / w
        small_test = cv2.resize(frame, (320, int(h * test_scale)))
        sh, sw = small_test.shape[:2]
        cx, cy = sw // 2, sh // 2
        tx1 = max(cx - CENTER_CROP_WIDTH // 2, 0)
        tx2 = min(cx + CENTER_CROP_WIDTH // 2, sw)
        ty1 = max(cy - CENTER_CROP_HEIGHT // 2, 0)
        ty2 = min(cy + CENTER_CROP_HEIGHT // 2, sh)
        cropped_test = small_test[ty1:ty2, tx1:tx2]

        success, buffer = cv2.imencode(".jpg", cropped_test, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not success:
            print("ERROR: Failed to encode frame as JPEG")
            mini.goto_sleep()
            return
        jpeg_bytes = buffer.tobytes()
        print(f"  Encoded frame: {len(jpeg_bytes)} bytes (center-cropped)")

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

        # Filter for target (offset boxes back to original frame coords)
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
                    box=(
                        int((box.xmin + tx1) / test_scale),
                        int((box.ymin + ty1) / test_scale),
                        int((box.xmax + tx1) / test_scale),
                        int((box.ymax + ty1) / test_scale),
                    ),
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

        # --- Shared detection state (written by detection thread, read by main loop) ---
        det_lock = threading.Lock()
        det_result: Detection | None = None
        det_frame_time: float = 0.0

        # Threading events
        stop_event = threading.Event()
        pause_event = threading.Event()  # set = paused

        def detection_loop() -> None:
            """Background thread: capture frames and run inference."""
            nonlocal det_result, det_frame_time
            interval = 1.0 / config.detection_hz
            max_age = 3.0  # discard if inference took too long

            while not stop_event.is_set():
                # Respect pause (scan-only window after reaction)
                if pause_event.is_set():
                    time.sleep(0.1)
                    continue

                loop_start = time.monotonic()

                frame_det = mini.media.get_frame()
                if frame_det is None:
                    time.sleep(0.1)
                    continue

                frame_capture_time = time.monotonic()

                # Resize and center-crop
                h, w = frame_det.shape[:2]
                scale = 320 / w
                small = cv2.resize(frame_det, (320, int(h * scale)))
                sh, sw = small.shape[:2]
                cx, cy = sw // 2, sh // 2
                x1 = max(cx - CENTER_CROP_WIDTH // 2, 0)
                x2 = min(cx + CENTER_CROP_WIDTH // 2, sw)
                y1 = max(cy - CENTER_CROP_HEIGHT // 2, 0)
                y2 = min(cy + CENTER_CROP_HEIGHT // 2, sh)
                cropped = small[y1:y2, x1:x2]

                success, buffer = cv2.imencode(
                    ".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, 65]
                )
                if not success:
                    continue
                jpeg = buffer.tobytes()

                try:
                    if config.endpoint_url:
                        results = run_endpoint_detection(
                            config.endpoint_url, config.hf_token, jpeg
                        )
                    else:
                        results = client.object_detection(
                            jpeg,
                            model=config.model,
                            threshold=config.confidence_threshold,
                        )
                except Exception as e:
                    print(f"  Detection error: {e}")
                    continue

                receipt_time = time.monotonic()
                if (receipt_time - frame_capture_time) > max_age:
                    continue  # stale

                found = None
                for r in results:
                    if (
                        r.label
                        and r.label.lower() == config.target_label.lower()
                        and r.score >= config.confidence_threshold
                    ):
                        box = r.box
                        found = Detection(
                            label=r.label,
                            score=r.score,
                            box=(
                                int((box.xmin + x1) / scale),
                                int((box.ymin + y1) / scale),
                                int((box.xmax + x1) / scale),
                                int((box.ymax + y1) / scale),
                            ),
                        )
                        break

                with det_lock:
                    det_result = found
                    if found is not None:
                        det_frame_time = frame_capture_time

                # Pace to detection_hz
                elapsed = time.monotonic() - loop_start
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        # Start detection thread
        det_thread = threading.Thread(target=detection_loop, daemon=True)
        det_thread.start()
        print("  Detection thread started")

        # --- Main control loop at control_hz using set_target ---
        control_interval = 1.0 / config.control_hz
        last_status_time = time.monotonic()
        last_reaction_time = 0.0

        try:
            while True:
                loop_start = time.monotonic()

                # Check if scan-only window has expired
                if pause_event.is_set():
                    if (loop_start - last_reaction_time) >= config.scan_only_duration:
                        pause_event.clear()
                        print(f"  Scan-only window ended, resuming detection")

                # Read latest detection from background thread
                with det_lock:
                    current_detection = det_result
                    good_frame_time = det_frame_time

                detection_age = (
                    (loop_start - good_frame_time) if good_frame_time > 0 else 999.0
                )

                # Update controller
                yaw, pitch, body_yaw, reaction_triggered = controller.update(
                    current_detection, detection_age
                )

                # React on detection
                if reaction_triggered:
                    last_reaction_time = loop_start
                    pause_event.set()  # pause detection thread
                    move = emotions.get(config.reaction_emotion)
                    print(f"  Reacting: {config.reaction_emotion}!")

                    if config.reaction_audio:
                        # Play custom audio (non-blocking), suppress built-in emotion sound
                        audio_path = os.path.join(
                            os.path.dirname(__file__), "assets", config.reaction_audio
                        )
                        try:
                            for play in range(NUM_PLAYS):
                                mini.media.play_sound(audio_path)
                        except Exception as e:
                            print(f"  (custom sound failed, continuing) {e}")
                        mini.play_move(move, initial_goto_duration=1.0, sound=False)
                    else:
                        # Let play_move handle the built-in emotion sound
                        mini.play_move(move, initial_goto_duration=1.0, sound=True)
                    controller.resume_scanning()
                    # Clear shared detection state
                    with det_lock:
                        det_result = None
                        det_frame_time = 0.0
                    print(f"  Scanning only for {config.scan_only_duration}s...")
                    continue

                # Non-blocking position command
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

                # Sleep to maintain control_hz
                elapsed = time.monotonic() - loop_start
                sleep_time = max(0, control_interval - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n\nStopping tracker (Ctrl+C received)...")

        stop_event.set()
        det_thread.join(timeout=2.0)
        mini.goto_sleep()
        print("Dog Tracker stopped.")


if __name__ == "__main__":
    main()
