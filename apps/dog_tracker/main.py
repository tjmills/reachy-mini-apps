"""Dog tracking app for Reachy Mini using remote HuggingFace inference."""

from __future__ import annotations

import time


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
        # Bring head out
        mini.wake_up()
        time.sleep(1.0)  # let the motion finish + camera settle
        print("Connected to Reachy Mini")
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
        client = InferenceClient(token=config.hf_token)

        # Encode frame as JPEG
        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not success:
            print("ERROR: Failed to encode frame as JPEG")
            mini.goto_sleep()
            return
        jpeg_bytes = buffer.tobytes()
        print(f"  Encoded frame: {len(jpeg_bytes)} bytes")

        # Run detection (uses default DETR model)
        try:
            results = client.object_detection(jpeg_bytes)
            print(f"  Raw API results: {len(results)} objects detected")
            for i, r in enumerate(results[:5]):  # Show first 5
                print(f"    [{i}] label={r.label}, score={r.score:.2f}, box={r.box}")
        except Exception as e:
            print(f"ERROR: Object detection failed: {e}")
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
            x_min, y_min, x_max, y_max = detection.box
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            label_text = f"{detection.label}: {detection.score:.2f}"
            cv2.putText(frame, label_text, (x_min, y_min - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.imwrite("./test_frame_annotated.png", frame)
            print("Saved test_frame_annotated.png with bounding box")

        mini.goto_sleep()
        print("Dog Tracker stopped.")


if __name__ == "__main__":
    main()
