"""DualGuard 메인 실행 엔트리포인트.

USB 웹캠에서 프레임을 받아 Stage 0(검출) → Stage 1(인식) → Stage 2(Anti-Spoofing)
3단계 검증을 수행하고, 결과에 따라 GPIO 액추에이터 제어, MQTT 발행, CSV 로그
기록을 수행하는 실시간 인증 루프를 구동한다.
"""

from __future__ import annotations


def main() -> None:
    """실시간 인증 루프 진입점.

    TODO:
        - 카메라 오픈 (config.CAMERA_INDEX)
        - 모듈 초기화: FaceDetector / FaceRecognizer / AntiSpoofing /
          Fusion / GPIOController / MQTTPublisher / DataManager
        - MQTT 시작 메시지 발행 (TOPIC_SYSTEM_STATUS)
        - 프레임 루프:
            1. 프레임 캡처
            2. 얼굴 검출 → 없으면 continue
            3. FaceNet 임베딩 + DB 매칭
            4. MiniFASNet Real/Spoof 분류
            5. fusion.decide()
            6. 결과에 따라 GPIO 동작 + MQTT 발행 + CSV 기록
            7. 미리보기 창에 박스/이름 오버레이
        - 종료 시 GPIO cleanup, MQTT 종료 메시지 발행
    """
    raise NotImplementedError("TODO: 실시간 인증 루프 구현")


if __name__ == "__main__":
    main()
