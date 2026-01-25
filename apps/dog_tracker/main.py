"""Dog tracking app for Reachy Mini using remote HuggingFace inference."""

from __future__ import annotations

import time
from dataclasses import dataclass


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


def run_endpoint_detection(endpoint_url: str, token: str, jpeg_bytes: bytes) -> list[DetResult]:
    """Run object detection on a dedicated HF endpoint."""
    import requests
    resp = requests.post(
        endpoint_url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "image/jpeg",
        },
        data=jpeg_bytes,
    )
    resp.raise_for_status()
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

        # Phase 3: Scanning motion test
        import numpy as np
        from controller import Controller
        from reachy_mini.utils import create_head_pose  # type: ignore

        print("\n=== Phase 3: Scanning Motion Test (10 seconds) ===")
        controller = Controller(config, frame_width, frame_height)

        scan_duration = 10.0
        scan_start = time.monotonic()
        last_status = scan_start

        while time.monotonic() - scan_start < scan_duration:
            yaw, pitch, _ = controller.update(detection=None, detection_age=2.0)
            # Use SDK set_target with head_pose for continuous control
            head_pose = create_head_pose(yaw=yaw, pitch=pitch, degrees=False)
            mini.set_target(head=head_pose)

            # Status every 2 seconds
            if time.monotonic() - last_status >= 2.0:
                print(
                    f"  Mode: {controller.mode.value}, "
                    f"Yaw: {np.rad2deg(yaw):.1f} deg, "
                    f"Pitch: {np.rad2deg(pitch):.1f} deg"
                )
                last_status = time.monotonic()

            time.sleep(1.0 / config.control_hz)

        print("Phase 3 complete: Scanning motion test finished")

        # Phase 4: Mock tracking test
        print("\n=== Phase 4: Mock Tracking Test ===")

        mock_positions = [
            ("CENTER", (640, 360)),
            ("LEFT", (200, 360)),
            ("RIGHT", (1080, 360)),
            ("UP", (640, 150)),
            ("DOWN", (640, 570)),
        ]

        for name, (cx, cy) in mock_positions:
            mock_detection = Detection(
                label="mock",
                score=0.99,
                box=(cx - 50, cy - 50, cx + 50, cy + 50),
            )
            print(f"  Testing {name} position ({cx}, {cy})...")

            test_duration = 2.0
            test_start = time.monotonic()
            while time.monotonic() - test_start < test_duration:
                yaw, pitch, _ = controller.update(mock_detection, detection_age=0.0)
                head_pose = create_head_pose(yaw=yaw, pitch=pitch, degrees=False)
                mini.set_target(head=head_pose)
                time.sleep(1.0 / config.control_hz)

            print(f"    Result: Yaw={np.rad2deg(yaw):.1f} deg, Pitch={np.rad2deg(pitch):.1f} deg")

        print("Phase 4 complete: Mock tracking test finished")

        # Phase 5: Full integration - continuous tracking
        print("\n=== Phase 5: Continuous Tracking (Ctrl+C to stop) ===")
        print("Robot will scan when no target visible, track when target detected")

        # Reset controller for clean state
        controller = Controller(config, frame_width, frame_height)

        loop_start_time = time.monotonic()
        last_inference_time = 0.0  # When we last ran inference
        last_good_frame_time = 0.0  # Frame capture time of last valid detection
        last_status_time = loop_start_time
        current_detection = None
        detection_interval = 1.0 / config.detection_hz
        consecutive_misses = 0  # Hysteresis counter

        # Latency tracking for p50/p95 stats
        latencies_ms: list[float] = []

        # Debug frame output (every 3 seconds when tracking)
        last_debug_frame_time = 0.0

        # Stale detection threshold - discard results older than this
        # Note: HF serverless can be slow (2-10s), adjust based on observed latency
        max_detection_age = 3.0  # seconds

        try:
            while True:
                loop_start = time.monotonic()

                # Run detection at detection_hz
                if loop_start - last_inference_time >= detection_interval:
                    frame = mini.media.get_frame()
                    if frame is not None:
                        # Timestamp when frame was captured (before inference)
                        frame_capture_time = time.monotonic()

                        # Resize frame to reduce latency (320px for lower network overhead)
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
                                latency_ms = (receipt_time - inference_start) * 1000
                                latencies_ms.append(latency_ms)
                                age_at_receipt = receipt_time - frame_capture_time

                                # Discard stale results (inference took too long)
                                if age_at_receipt > max_detection_age:
                                    print(f"  Discarding stale detection ({age_at_receipt:.1f}s > {max_detection_age}s)")
                                else:
                                    # Look for target in results
                                    found_detection = None
                                    for r in results:
                                        if r.label and r.label.lower() == config.target_label.lower():
                                            box = r.box
                                            # Scale box back to original frame size
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

                                    # Update detection state
                                    if found_detection is not None:
                                        current_detection = found_detection
                                        last_good_frame_time = frame_capture_time
                                        consecutive_misses = 0

                                        # Save debug frame every 3 seconds when tracking
                                        if loop_start - last_debug_frame_time >= 3.0:
                                            debug_frame = frame.copy()
                                            x1, y1, x2, y2 = found_detection.box
                                            cv2.rectangle(debug_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                            # Draw frame center crosshair
                                            fx, fy = frame_width // 2, frame_height // 2
                                            cv2.line(debug_frame, (fx - 20, fy), (fx + 20, fy), (0, 0, 255), 2)
                                            cv2.line(debug_frame, (fx, fy - 20), (fx, fy + 20), (0, 0, 255), 2)
                                            cv2.imwrite(f"./debug_frame_{int(loop_start)}.png", debug_frame)
                                            print(f"  Debug: det@{found_detection.center}, center@({fx},{fy})")
                                            last_debug_frame_time = loop_start
                                    else:
                                        consecutive_misses += 1
                            except Exception as e:
                                print(f"  Detection error: {e}")
                                consecutive_misses += 1
                    last_inference_time = loop_start

                # Compute detection age based on when frame was captured (not receipt time)
                detection_age = (
                    (loop_start - last_good_frame_time)
                    if last_good_frame_time > 0
                    else 999.0
                )

                # Update controller (hysteresis: need 3+ misses before age matters for scanning)
                # This prevents "track → scan → track" flicker
                effective_age = detection_age if consecutive_misses >= 3 else min(detection_age, 0.5)
                yaw, pitch, _ = controller.update(current_detection, effective_age)
                head_pose = create_head_pose(yaw=yaw, pitch=pitch, degrees=False)
                mini.set_target(head=head_pose)

                # Status every 3 seconds
                if loop_start - last_status_time >= 3.0:
                    det_str = f"{current_detection.label}" if current_detection else "None"
                    print(
                        f"  Mode: {controller.mode.value}, "
                        f"Detection: {det_str}, "
                        f"Age: {detection_age:.1f}s, "
                        f"Yaw: {np.rad2deg(yaw):.1f} deg"
                    )
                    last_status_time = loop_start

                # Sleep to maintain control rate
                elapsed = time.monotonic() - loop_start
                sleep_time = max(0, (1.0 / config.control_hz) - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n\nStopping tracker (Ctrl+C received)...")

        # Print latency statistics
        if latencies_ms:
            sorted_latencies = sorted(latencies_ms)
            n = len(sorted_latencies)
            p50 = sorted_latencies[n // 2]
            p95 = sorted_latencies[int(n * 0.95)] if n >= 20 else sorted_latencies[-1]
            print(f"\nLatency stats ({n} samples):")
            print(f"  p50: {p50:.0f}ms")
            print(f"  p95: {p95:.0f}ms")
            print(f"  min: {sorted_latencies[0]:.0f}ms")
            print(f"  max: {sorted_latencies[-1]:.0f}ms")

        mini.goto_sleep()
        print("Dog Tracker stopped.")


if __name__ == "__main__":
    main()
