from __future__ import annotations

import argparse
import logging
import math
import os
import sys
import threading
import time
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

import numpy as np
import torch

try:
    from supervision import Detections
    from ultralytics import YOLO  # type: ignore
except ImportError as e:
    raise ImportError(
        "To use YOLO tracking, install the extra dependencies: pip install '.[yolo_vision]'",
    ) from e
from huggingface_hub import hf_hub_download

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


MODEL_REPO = ""
MODEL_FILENAME = "yolov8n.pt"
DEFAULT_TARGET = "person"
logger = logging.getLogger(__name__)


@dataclass
class Config:
    target_label: str
    conf_thresh: float
    model_repo: str
    model_filename: str

    hz: float
    smooth_alpha: float
    kp_yaw: float
    kp_pitch: float

    max_yaw_deg: float
    max_pitch_deg: float

    deadband_px: int
    lost_timeout_s: float

    scan_yaw_amp_deg: float
    scan_period_s: float
    scan_pitch_deg: float


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


class YoloDetector:
    def __init__(self, model_repo: str, model_filename: str, device: str) -> None:
        model_path = model_filename
        if model_repo:
            try:
                token = os.getenv("HF_TOKEN")
                model_path = hf_hub_download(
                    repo_id=model_repo,
                    filename=model_filename,
                    token=token,
                )
                logger.info("Downloaded YOLO model from %s/%s", model_repo, model_filename)
            except Exception as e:
                logger.warning(
                    "Failed to download YOLO model from Hugging Face (%s). "
                    "Falling back to local/ultralytics download of %s.",
                    e,
                    model_filename,
                )
                model_path = model_filename

        self.model = YOLO(model_path).to(device)
        if model_repo:
            logger.info("Loaded YOLO model %s on %s", model_path, device)
        else:
            logger.info("Loaded YOLO model %s on %s", model_filename, device)

    def detect(self, frame: np.ndarray) -> tuple[Detections, dict[int, str]]:
        results = self.model(frame, verbose=False)
        return Detections.from_ultralytics(results[0]), results[0].names


def pick_best_detection(
    detections: Detections,
    class_names: dict[int, str],
    target_label: str,
    conf_thresh: float,
) -> np.ndarray | None:
    if detections.xyxy.shape[0] == 0:
        return None
    if detections.confidence is None or detections.class_id is None:
        return None

    mask = detections.confidence >= conf_thresh
    if target_label:
        target = target_label.lower()
        class_ids = np.asarray(detections.class_id, dtype=int)
        name_mask = np.array(
            [class_names.get(int(cid), "").lower() == target for cid in class_ids],
            dtype=bool,
        )
        mask = mask & name_mask

    if not np.any(mask):
        return None

    indices = np.where(mask)[0]
    boxes = detections.xyxy[indices]
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    best_idx = indices[np.argmax(areas)]
    return detections.xyxy[best_idx]


def run_tracking_loop(
    mini: ReachyMini,
    cfg: Config,
    stop_event: threading.Event | None = None,
) -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    detector = YoloDetector(cfg.model_repo, cfg.model_filename, device=device)

    # Smoothed normalized offsets
    sdx, sdy = 0.0, 0.0

    # Head angles
    yaw_deg, pitch_deg = 0.0, 0.0

    last_seen = 0.0
    dt = 1.0 / cfg.hz
    t0 = time.time()

    print("Connected. Starting tracking loop.")

    while True:
        if stop_event is not None and stop_event.is_set():
            logger.info("Stop event detected. Exiting tracking loop.")
            return

        loop_start = time.time()

        # -------- Camera (official SDK pattern)
        frame = mini.media.get_frame()
        if frame is None:
            continue

        # Frame is BGR np.ndarray
        h, w = frame.shape[:2]
        cx, cy = w / 2, h / 2

        detections, class_names = detector.detect(frame)
        bbox = pick_best_detection(
            detections,
            class_names,
            cfg.target_label,
            cfg.conf_thresh,
        )

        if bbox is not None:
            last_seen = time.time()

            tx = (bbox[0] + bbox[2]) / 2
            ty = (bbox[1] + bbox[3]) / 2

            dx_px = tx - cx
            dy_px = ty - cy

            if abs(dx_px) < cfg.deadband_px:
                dx_px = 0.0
            if abs(dy_px) < cfg.deadband_px:
                dy_px = 0.0

            dx = dx_px / (w / 2)
            dy = dy_px / (h / 2)

            sdx = cfg.smooth_alpha * sdx + (1 - cfg.smooth_alpha) * dx
            sdy = cfg.smooth_alpha * sdy + (1 - cfg.smooth_alpha) * dy

            yaw_deg += cfg.kp_yaw * sdx
            pitch_deg += cfg.kp_pitch * (-sdy)

        else:
            # Idle scan if target lost
            if time.time() - last_seen > cfg.lost_timeout_s:
                t = time.time() - t0
                yaw_deg = cfg.scan_yaw_amp_deg * math.sin(
                    2 * math.pi * t / cfg.scan_period_s
                )
                pitch_deg = cfg.scan_pitch_deg

        yaw_deg = clamp(yaw_deg, -cfg.max_yaw_deg, cfg.max_yaw_deg)
        pitch_deg = clamp(pitch_deg, -cfg.max_pitch_deg, cfg.max_pitch_deg)

        # -------- Motion (official SDK pattern)
        pose = create_head_pose(
            z=0.0,
            roll=0.0,
            pitch=pitch_deg,
            yaw=yaw_deg,
            degrees=True,
            mm=True,
        )

        mini.set_target(head=pose)

        # -------- Rate limiting
        elapsed = time.time() - loop_start
        if elapsed < dt:
            time.sleep(dt - elapsed)


def _log_remote_media_hints() -> None:
    try:
        version = metadata.version("reachy-mini")
    except metadata.PackageNotFoundError:
        version = "unknown"

    logger.warning(
        "Remote media requires WebRTC; with reachy-mini==1.2.4 you may need system GStreamer + "
        "gst_signalling (or downgrade to 1.2.3). Detected reachy-mini=%s.",
        version,
    )


def _configure_macos_gstreamer_env() -> None:
    if sys.platform != "darwin":
        return

    prefixes = [Path("/opt/homebrew"), Path("/usr/local")]
    for prefix in prefixes:
        lib_dir = prefix / "lib"
        gi_dir = lib_dir / "girepository-1.0"
        gst_dir = lib_dir / "gstreamer-1.0"
        if not lib_dir.exists():
            continue

        if os.environ.get("DYLD_LIBRARY_PATH") is None and (lib_dir / "libglib-2.0.0.dylib").exists():
            os.environ["DYLD_LIBRARY_PATH"] = str(lib_dir)
        if os.environ.get("GI_TYPELIB_PATH") is None and gi_dir.exists():
            os.environ["GI_TYPELIB_PATH"] = str(gi_dir)
        if os.environ.get("GST_PLUGIN_PATH") is None and gst_dir.exists():
            os.environ["GST_PLUGIN_PATH"] = str(gst_dir)

    if os.environ.get("GI_TYPELIB_PATH") is None:
        logger.warning(
            "GI_TYPELIB_PATH is unset; install GStreamer + gobject-introspection via Homebrew "
            "and ensure its girepository path is available.",
        )
    if os.environ.get("GST_PLUGIN_PATH") is None:
        logger.warning(
            "GST_PLUGIN_PATH is unset; install gst-plugins-base/good/bad/ugly via Homebrew.",
        )


def main(cfg: Config, *, wireless_version: bool, on_device: bool) -> None:
    print(f"Tracking target: '{cfg.target_label}'")
    try:
        if wireless_version and not on_device:
            _configure_macos_gstreamer_env()
            logger.info("Using WebRTC backend for fully remote wireless version")
            mini_ctx = ReachyMini(media_backend="webrtc", localhost_only=False)
        elif wireless_version and on_device:
            logger.info("Using GStreamer backend for on-device wireless version")
            mini_ctx = ReachyMini(media_backend="gstreamer")
        else:
            logger.info("Using default backend for lite version")
            mini_ctx = ReachyMini(media_backend="default")
    except (ModuleNotFoundError, ValueError):
        if wireless_version and not on_device:
            _log_remote_media_hints()
        raise

    try:
        with mini_ctx as mini:
            if mini.media.camera is None:
                if wireless_version and not on_device:
                    logger.error(
                        "Camera is not initialized (media_backend=%s). "
                        "For laptop use, start the daemon with '--stream' to enable WebRTC.",
                        mini.media.backend.value,
                    )
                else:
                    logger.error(
                        "Camera is not initialized (media_backend=%s). "
                        "Use the on-device wireless mode or enable streaming on the robot.",
                        mini.media.backend.value,
                    )
                return

            run_tracking_loop(mini, cfg, stop_event=None)
    except Exception:
        if wireless_version and not on_device:
            _log_remote_media_hints()
        logger.exception("Reachy Mini initialization failed during tracking startup")
        raise


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default=DEFAULT_TARGET)
    ap.add_argument("--conf", type=float, default=0.7)
    ap.add_argument(
        "--model-repo",
        default=MODEL_REPO,
        help="Optional Hugging Face repo_id for YOLO weights (set HF_TOKEN for gated repos).",
    )
    ap.add_argument("--model-file", default=MODEL_FILENAME, help="Model filename or local path.")
    ap.add_argument("--hz", type=float, default=15.0)
    ap.add_argument(
        "--wireless-version",
        default=False,
        action="store_true",
        help="Use WebRTC or GStreamer backend for wireless versions.",
    )
    ap.add_argument(
        "--on-device",
        default=False,
        action="store_true",
        help="Use when running on the same device as the Reachy Mini daemon (wireless).",
    )
    return ap.parse_args()


def build_config(args: argparse.Namespace) -> Config:
    return Config(
        target_label=args.target,
        conf_thresh=args.conf,
        model_repo=args.model_repo,
        model_filename=args.model_file,
        hz=args.hz,
        smooth_alpha=0.85,
        kp_yaw=2.5,
        kp_pitch=2.0,
        max_yaw_deg=55.0,
        max_pitch_deg=25.0,
        deadband_px=18,
        lost_timeout_s=1.0,
        scan_yaw_amp_deg=20.0,
        scan_period_s=6.0,
        scan_pitch_deg=5.0,
    )


def main_from_cli() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s:%(lineno)d | %(message)s",
    )
    args = parse_args()
    cfg = build_config(args)
    main(cfg, wireless_version=args.wireless_version, on_device=args.on_device)
