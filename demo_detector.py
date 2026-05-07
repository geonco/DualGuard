"""face_detector 수동 데모 — Week 1 DoD 확인용.

VNC로 Pi 데스크톱 들어와서 실행. 카메라 미리보기에 얼굴 박스가 그려지면 OK.
'q' 키로 종료.
"""

from __future__ import annotations

import time

import cv2

import config
from modules.face_detector import FaceDetector


def main() -> None:
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    if not cap.isOpened():
        raise RuntimeError(f"카메라 열기 실패: index={config.CAMERA_INDEX}")

    last = time.time()
    fps = 0.0

    with FaceDetector(min_confidence=0.5) as detector:
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    print("프레임 캡처 실패")
                    break

                boxes = detector.detect(frame)
                for x, y, w, h in boxes:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                now = time.time()
                fps = 0.9 * fps + 0.1 * (1.0 / max(now - last, 1e-6))
                last = now
                cv2.putText(
                    frame,
                    f"faces={len(boxes)}  fps={fps:.1f}",
                    (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                cv2.imshow("DualGuard - face detector demo (q=quit)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
