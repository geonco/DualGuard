"""신규 사용자 등록 스크립트 (명세서 F1).

카메라로 다양한 각도에서 ``REGISTER_NUM_SAMPLES`` 장을 자동 캡처하여
FaceNet 임베딩의 평균 벡터를 계산하고, users.json 및 embeddings.npy에 저장한다.

사용법:
    python register.py                  # 이름 입력 프롬프트
    python register.py --name 임건우    # 이름 인자 직접
"""

from __future__ import annotations

import argparse
import sys
import time

import cv2

import config
from modules.data_manager import DataManager
from modules.face_detector import FaceDetector
from modules.face_recognizer import FaceRecognizer

CAPTURE_INTERVAL_SEC = 0.6  # 다양한 각도/표정 유도용
SAMPLES_DIR = config.DATA_DIR / "registered_samples"


def _draw_overlay(frame, text: str, count: int, total: int) -> None:
    h = frame.shape[0]
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 35), (0, 0, 0), -1)
    cv2.putText(frame, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.rectangle(frame, (0, h - 35), (frame.shape[1], h), (0, 0, 0), -1)
    cv2.putText(
        frame,
        f"captured {count}/{total}",
        (10, h - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
    )


def register_user(name: str) -> None:
    """단일 사용자 등록 처리.

    Args:
        name: 호출 측에서 ``resolve_unique_name`` 으로 suffix까지 부여된 최종 이름.
    """
    dm = DataManager()
    detector = FaceDetector(min_confidence=0.5)
    recognizer = FaceRecognizer(data_manager=dm)

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    if not cap.isOpened():
        raise RuntimeError(f"카메라 열기 실패: index={config.CAMERA_INDEX}")

    embeddings: list = []
    target = config.REGISTER_NUM_SAMPLES
    last_capture = 0.0

    sample_dir = SAMPLES_DIR / name
    sample_dir.mkdir(parents=True, exist_ok=True)
    print(f"[register] Starting registration for '{name}'.")
    print(f"[register] Look at the camera and slowly vary your angle/expression.")
    print(f"[register] Capturing {target} samples. Press ESC to cancel.")

    try:
        while len(embeddings) < target:
            ok, frame = cap.read()
            if not ok:
                continue

            bbox = detector.detect_largest(frame)
            now = time.time()

            if bbox is None:
                _draw_overlay(frame, "No face detected", len(embeddings), target)
            else:
                x, y, w, h = bbox
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                if now - last_capture >= CAPTURE_INTERVAL_SEC:
                    face = detector.crop(frame, bbox, margin=0.2)
                    try:
                        emb = recognizer.embed(face)
                        embeddings.append(emb)
                        sample_path = sample_dir / f"{len(embeddings):02d}.jpg"
                        cv2.imwrite(str(sample_path), face)
                        last_capture = now
                        print(f"[register] captured {len(embeddings)}/{target} -> {sample_path}")
                    except Exception as e:
                        print(f"[register] capture failed: {e}")

                _draw_overlay(frame, f"Registering: {name}", len(embeddings), target)

            cv2.imshow("DualGuard - register (ESC=cancel)", frame)
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                print("[register] Cancelled by user")
                return

    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.close()

    if len(embeddings) < target:
        print(f"[register] Not enough samples ({len(embeddings)}/{target}) — aborted")
        return

    # 평균 벡터 → L2 정규화
    import numpy as np

    mean_emb = np.mean(np.stack(embeddings), axis=0)
    mean_emb = mean_emb / max(np.linalg.norm(mean_emb), 1e-10)

    idx = dm.add_user(name, mean_emb.astype(np.float32))
    print(f"[register] Done. '{name}' registered (embedding_index={idx})")


def main() -> None:
    parser = argparse.ArgumentParser(description="DualGuard 사용자 등록")
    parser.add_argument("--name", type=str, default=None, help="등록할 사용자 이름")
    args = parser.parse_args()

    name = args.name
    if not name:
        try:
            name = input("Name to register: ").strip()
        except EOFError:
            name = ""
    if not name:
        print("[register] Empty name.", file=sys.stderr)
        sys.exit(1)

    dm = DataManager()
    final_name = dm.resolve_unique_name(name)
    if final_name != name:
        print(f"[register] Name collision -> registering as '{final_name}'")

    register_user(final_name)


if __name__ == "__main__":
    main()
