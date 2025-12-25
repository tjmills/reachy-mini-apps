from __future__ import annotations

import os
import threading

from reachy_mini.apps.app import ReachyMiniApp

from tracker import Config, run_tracking_loop


class TargetTrackingApp(ReachyMiniApp):
    """Reachy Mini app entrypoint for target tracking."""

    dont_start_webserver = True

    def run(self, reachy_mini, stop_event: threading.Event) -> None:  # type: ignore[override]
        target_label = os.getenv("TARGET_TRACKING_LABEL", "person")
        conf_thresh = float(os.getenv("TARGET_TRACKING_CONF", "0.7"))
        hz = float(os.getenv("TARGET_TRACKING_HZ", "15.0"))
        model_repo = os.getenv("TARGET_TRACKING_MODEL_REPO", "")
        model_file = os.getenv("TARGET_TRACKING_MODEL_FILE", "yolov8n.pt")

        cfg = Config(
            target_label=target_label,
            conf_thresh=conf_thresh,
            model_repo=model_repo,
            model_filename=model_file,
            hz=hz,
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

        run_tracking_loop(reachy_mini, cfg, stop_event=stop_event)


def main() -> None:
    app = TargetTrackingApp()
    app.wrapped_run()


if __name__ == "__main__":
    main()
