"""face_recognizer 수동 데모 — Week 2 DoD 확인용.

등록 DB와 코사인 유사도로 매칭한 결과를 카메라 화면에 그린다.
- 등록자 매칭: 초록 박스 + "name (score)"
- Unknown:     빨간 박스 + "Unknown (score)"
'q' 키로 종료.
"""

from __future__ import annotations

import time

import cv2

import config
from modules.data_manager import DataManager
from modules.face_detector import FaceDetector
from modules.face_recognizer import FaceRecognizer


def main() -> None:
    dm = DataManager()
    if not config.USERS_JSON.exists() or not config.EMBEDDINGS_NPY.exists():
        print("No registered users. Run `python register.py --name <you>` first.")
        return

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open camera: index={config.CAMERA_INDEX}")

    detector = FaceDetector(min_confidence=0.5)
    recognizer = FaceRecognizer(data_manager=dm)

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
                face = detector.crop(frame, bbox, margin=0.2)
                try:
                    name, score, _ = recognizer.identify(face)
                    if name is not None:
                        label = f"{name}  sim={score:.2f}"
                        color = (0, 255, 0)
                    else:
                        label = f"Unknown  sim={score:.2f}"
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
                frame, f"fps={fps:.1f}  threshold={config.FACENET_SIM_THRESHOLD}",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2,
            )

            cv2.imshow("DualGuard - recognizer demo (q=quit)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.close()


if __name__ == "__main__":
    main()
