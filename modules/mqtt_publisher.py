"""MQTT 발행 모듈 (명세서 F4).

paho-mqtt로 로컬 Mosquitto 브로커(localhost:1883)에 인증 이벤트를 publish 한다.

토픽:
    - dualguard/access/granted : 통과 시
    - dualguard/access/denied  : 차단 시
    - dualguard/system/status  : 시작/종료 시
"""

from __future__ import annotations

from typing import Optional


class MQTTPublisher:
    """단방향 publish 전용 MQTT 클라이언트 래퍼."""

    def __init__(self, host: str, port: int, client_id: str,
                 keepalive: int = 60) -> None:
        """클라이언트 생성 및 연결.

        TODO:
            - paho.mqtt.client.Client(client_id) 생성
            - on_connect / on_disconnect 콜백 등록
            - connect(host, port, keepalive)
            - loop_start() (백그라운드 스레드)
        """
        raise NotImplementedError

    def publish_granted(self, user: str, confidence: float) -> None:
        """통과 이벤트 발행. payload = {time, user, confidence}. TODO."""
        raise NotImplementedError

    def publish_denied(self, reason: str, confidence: float) -> None:
        """차단 이벤트 발행. payload = {time, reason, confidence}. TODO."""
        raise NotImplementedError

    def publish_status(self, status: str) -> None:
        """시스템 상태 발행. payload = {time, status}. TODO."""
        raise NotImplementedError

    def close(self) -> None:
        """loop_stop() + disconnect(). TODO."""
        raise NotImplementedError

    # ---- 내부 -------------------------------------------------------------
    def _publish_json(self, topic: str, payload: dict,
                      qos: int = 0, retain: bool = False) -> None:
        """JSON 직렬화 + publish. TODO."""
        raise NotImplementedError
