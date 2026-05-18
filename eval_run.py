"""Evaluation capture script (spec 9.1 / 9.3).

Run the full Stage 0 -> Stage 1 -> Stage 2 pipeline on demand and log each
sample to data/eval_log.csv together with a manually supplied scenario label.
Unlike main.py this script:
  - never deduplicates (every SPACE press = one logged row),
  - records the raw facenet/fasnet scores so single-vs-dual comparison can
    be reconstructed offline,
  - tags each row with the attack scenario label, which the runtime CSV
    (access_log.csv) does not carry.

Usage:
    python eval_run.py --label real_self   --n 10
    python eval_run.py --label phone_self  --n 10
    python eval_run.py --label phone_other --n 10

Press SPACE in the preview window to capture one sample. Press q/ESC to quit
early. After N samples the script exits automatically.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

import cv2

import config
from modules.anti_spoofing import AntiSpoofing
from modules.data_manager import DataManager
from modules.face_detector import FaceDetector
from modules.face_recognizer import FaceRecognizer
from modules.fusion import decide_and, decide_weighted

VALID_LABELS = ("real_self", "phone_self", "phone_other")

EVAL_LOG_CSV = config.DATA_DIR / "eval_log.csv"
EVAL_LOG_HEADER = [
    "timestamp", "label", "matched_user",
    "facenet_score", "fasnet_score",
    "face_pass", "fas_pass",
    "dual_and_pass", "dual_weighted_pass",
]


def _ensure_csv() -> None:
    EVAL_LOG_CSV.parent.mkdir(parents=True, exist_ok=True)
    if not EVAL_LOG_CSV.exists():
        with EVAL_LOG_CSV.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(EVAL_LOG_HEADER)


def _append_row(row: list) -> None:
    with EVAL_LOG_CSV.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, choices=VALID_LABELS)
    ap.add_argument("--n", type=int, default=10, help="samples to capture")
    args = ap.parse_args()

    _ensure_csv()

    dm = DataManager()
    detector = FaceDetector(min_confidence=0.5)
    recognizer = FaceRecognizer(data_manager=dm)
    spoof = AntiSpoofing()

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open camera: index={config.CAMERA_INDEX}")

    print(f"[eval] label={args.label}  target={args.n} samples")
    print("[eval] SPACE = capture one sample, q/ESC = quit")

    captured = 0
    try:
        while captured < args.n:
            ok, frame = cap.read()
            if not ok:
                continue

            bbox = detector.detect_largest(frame)
            display = frame.copy()
            if bbox is not None:
                x, y, w, h = bbox
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                display,
                f"label={args.label}  {captured}/{args.n}  SPACE=capture",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2,
            )
            cv2.imshow("DualGuard - eval (SPACE/q)", display)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key != ord(" "):
                continue
            if bbox is None:
                print("[eval] no face detected, skip")
                continue

            face = detector.crop(frame, bbox, margin=0.2)
            user, face_score, _emb = recognizer.identify(face)
            fas_score = spoof.predict_real_score(frame, bbox)

            face_pass = (user is not None) and (face_score >= config.FACENET_SIM_THRESHOLD)
            fas_pass = fas_score >= config.FASNET_REAL_THRESHOLD

            dual_and = decide_and(
                user, face_score, fas_score,
                config.FACENET_SIM_THRESHOLD, config.FASNET_REAL_THRESHOLD,
            ).passed
            dual_w = decide_weighted(
                user, face_score, fas_score,
                config.FUSION_ALPHA, config.FUSION_BETA,
                config.FUSION_COMBINED_THRESHOLD,
            ).passed

            row = [
                datetime.now().isoformat(timespec="seconds"),
                args.label,
                user or "",
                f"{face_score:.4f}",
                f"{fas_score:.4f}",
                int(face_pass), int(fas_pass),
                int(dual_and), int(dual_w),
            ]
            _append_row(row)
            captured += 1
            print(
                f"[eval] #{captured:02d}  user={user or '-':>8}  "
                f"face={face_score:.3f}({'P' if face_pass else 'F'})  "
                f"fas={fas_score:.3f}({'P' if fas_pass else 'F'})  "
                f"dual_and={'P' if dual_and else 'F'}  dual_w={'P' if dual_w else 'F'}"
            )
    except KeyboardInterrupt:
        print("\n[eval] interrupted")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.close()
        print(f"[eval] done. wrote {captured} rows to {EVAL_LOG_CSV}")


if __name__ == "__main__":
    main()
