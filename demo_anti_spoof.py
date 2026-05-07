"""anti_spoofing 수동 데모.

본인 얼굴(Real) vs 사진/영상(Spoof) 보일 때 Real score 차이를 실시간으로 확인.
- score >= threshold(기본 0.5): 초록 박스 + "Real"
- score <  threshold:           빨간 박스 + "Spoof"
'q' 키로 종료.
"""

from __future__ import annotations

import time

import cv2

import config
from modules.anti_spoofing import AntiSpoofing
from modules.face_detector import FaceDetector


def main() -> None:
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open camera: index={config.CAMERA_INDEX}")

    detector = FaceDetector(min_confidence=0.5)
    spoof = AntiSpoofing()

    last = time.time()
    fps = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            bbox = detector.detect_largest(frame)
            label = "no face"
            color = (200, 200, 200)

            if bbox is not None:
                x, y, w, h = bbox
                try:
                    is_real, score = spoof.predict(frame, bbox)
                    if is_real:
                        label = f"Real  score={score:.2f}"
                        color = (0, 255, 0)
                    else:
                        label = f"Spoof score={score:.2f}"
                        color = (0, 0, 255)
                except Exception as e:
                    label = f"err: {e}"
                    color = (0, 0, 255)

                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(
                    frame, label, (x, max(20, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2,
                )

            now = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(now - last, 1e-6))
            last = now
            cv2.putText(
                frame, f"fps={fps:.1f}  threshold={config.FASNET_REAL_THRESHOLD}",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2,
            )

            cv2.imshow("DualGuard - anti-spoof demo (q=quit)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.close()


if __name__ == "__main__":
    main()
