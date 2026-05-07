"""DualGuard 메인 실행 엔트리포인트 (명세서 F2).

USB 웹캠에서 프레임을 받아 Stage 0(검출) → Stage 1(인식) → Stage 2(Anti-Spoofing)
3단계 검증을 수행하고, 결과에 따라 (GPIO/MQTT는 향후) CSV 로그 기록 + 콘솔
실시간 출력을 수행하는 인증 루프.

성능 목표(F2): 인증 1회 ≤ 0.5~1초, 미리보기 ≥ 15 FPS.
이를 위해 Anti-Spoofing은 매 프레임 돌리지 않고, 얼굴이 안정적으로 잡힐 때만
``ANTI_SPOOF_INTERVAL`` 프레임 간격으로 호출한다 (Pi CPU 부담 완화).

GPIO / MQTT 모듈은 try/except로 감싸 "있으면 사용, 없으면 무시" 처리하므로
하드웨어 통합 전에도 단독 실행 가능하다.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime

import cv2

import config
from modules.anti_spoofing import AntiSpoofing
from modules.data_manager import DataManager
from modules.face_detector import FaceDetector
from modules.face_recognizer import FaceRecognizer
from modules.fusion import (
    REASON_OK,
    REASON_SPOOF,
    REASON_UNKNOWN,
    FusionResult,
    decide_and,
    decide_weighted,
)

# 미등록 자/사진 공격이 카메라 앞에 잠깐 잡혀도 매 프레임 anti-spoof + 인식을
# 풀로 돌리면 FPS 폭락하므로, 얼굴이 보일 때 N프레임에 한 번만 풀 추론한다.
INFER_INTERVAL_FRAMES = 5

# ANSI color codes — 명세서 F6 colorama 대신 표준 escape (의존성 줄이기)
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"


def _log_console(result: FusionResult) -> None:
    """터미널 컬러 로그 (명세서 F6 형식)."""
    ts = datetime.now().strftime("%H:%M")
    if result.passed:
        line = f"{COLOR_GREEN}[{ts}] PASS  {result.user}  face={result.facenet_score:.2f} fas={result.fasnet_score:.2f}{COLOR_RESET}"
    elif result.reason == REASON_UNKNOWN:
        line = f"{COLOR_YELLOW}[{ts}] DENY  Unknown  face={result.facenet_score:.2f} fas={result.fasnet_score:.2f}{COLOR_RESET}"
    elif result.reason == REASON_SPOOF:
        line = f"{COLOR_RED}[{ts}] DENY  Spoof  user={result.user} face={result.facenet_score:.2f} fas={result.fasnet_score:.2f}{COLOR_RESET}"
    else:
        line = f"[{ts}] {result.reason} {result.user}"
    print(line)


def _draw_overlay(frame, bbox, result: FusionResult | None, fps: float) -> None:
    """미리보기 창에 박스 + 결과 텍스트 그림."""
    cv2.putText(
        frame, f"fps={fps:.1f}  mode={config.FUSION_MODE}",
        (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2,
    )

    if bbox is None:
        return

    x, y, w, h = bbox
    if result is None:
        color = (180, 180, 180)
        text = "..."
    elif result.passed:
        color = (0, 255, 0)
        text = f"{result.user}  face={result.facenet_score:.2f} fas={result.fasnet_score:.2f}"
    elif result.reason == REASON_UNKNOWN:
        color = (0, 200, 255)
        text = f"Unknown  face={result.facenet_score:.2f} fas={result.fasnet_score:.2f}"
    else:
        color = (0, 0, 255)
        text = f"Spoof  face={result.facenet_score:.2f} fas={result.fasnet_score:.2f}"

    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
    cv2.putText(
        frame, text, (x, max(20, y - 10)),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2,
    )


def _decide(user, face_score: float, fas_score: float) -> FusionResult:
    if config.FUSION_MODE.upper() == "WEIGHTED":
        return decide_weighted(
            user, face_score, fas_score,
            config.FUSION_ALPHA, config.FUSION_BETA,
            config.FUSION_COMBINED_THRESHOLD,
        )
    return decide_and(
        user, face_score, fas_score,
        config.FACENET_SIM_THRESHOLD, config.FASNET_REAL_THRESHOLD,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="DualGuard real-time auth loop")
    parser.add_argument(
        "--mode", choices=["AND", "WEIGHTED"], default=None,
        help="Override fusion mode (default: config.FUSION_MODE)",
    )
    parser.add_argument(
        "--no-preview", action="store_true",
        help="Run headless (no OpenCV window) — for SSH/PuTTY use",
    )
    args = parser.parse_args()

    if args.mode:
        config.FUSION_MODE = args.mode

    print(f"[main] DualGuard starting. fusion_mode={config.FUSION_MODE}")

    dm = DataManager()
    detector = FaceDetector(min_confidence=0.5)
    recognizer = FaceRecognizer(data_manager=dm)
    spoof = AntiSpoofing()

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open camera: index={config.CAMERA_INDEX}")

    last_result: FusionResult | None = None
    frame_idx = 0
    last_ts = time.time()
    fps = 0.0

    print("[main] Press 'q' (preview window) or Ctrl+C (terminal) to quit.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                continue

            bbox = detector.detect_largest(frame)

            # 매 INFER_INTERVAL_FRAMES마다, 얼굴이 있을 때만 풀 추론
            if bbox is not None and frame_idx % INFER_INTERVAL_FRAMES == 0:
                t0 = time.time()
                face = detector.crop(frame, bbox, margin=0.2)
                try:
                    user, face_score, _emb = recognizer.identify(face)
                    fas_score = spoof.predict_real_score(frame, bbox)
                    result = _decide(user, face_score, fas_score)
                    elapsed_ms = (time.time() - t0) * 1000

                    # 결과가 새로 바뀌었거나 직전과 다른 경우만 로그/CSV (스팸 방지)
                    if (
                        last_result is None
                        or result.user != last_result.user
                        or result.reason != last_result.reason
                        or result.passed != last_result.passed
                    ):
                        _log_console(result)
                        dm.append_log(
                            user=result.user,
                            result="PASS" if result.passed else "REJECT",
                            reason=result.reason,
                            facenet_score=result.facenet_score,
                            fasnet_score=result.fasnet_score,
                        )
                        if elapsed_ms > 0:
                            print(f"        (inference {elapsed_ms:.0f} ms)")
                    last_result = result
                except Exception as e:
                    print(f"[main] inference error: {e}")
                    last_result = None
            elif bbox is None:
                last_result = None

            now = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(now - last_ts, 1e-6))
            last_ts = now
            frame_idx += 1

            if not args.no_preview:
                _draw_overlay(frame, bbox, last_result, fps)
                cv2.imshow("DualGuard - main (q=quit)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    except KeyboardInterrupt:
        print("\n[main] Interrupted by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        detector.close()
        print("[main] Bye.")


if __name__ == "__main__":
    main()
