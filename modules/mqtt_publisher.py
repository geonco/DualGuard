"""MQTT 발행 모듈 (명세서 F4).

paho-mqtt로 로컬 Mosquitto 브로커(localhost:1883)에 인증 이벤트를 publish 한다.

토픽:
    - dualguard/access/granted : 통과 시
    - dualguard/access/denied  : 차단 시
    - dualguard/system/status  : 시작/종료 시

브로커 미가동 환경(개발 머신 등)을 위해 ``connect`` 실패 시 예외를 던지지 않고
no-op 모드로 떨어지도록 설계 — main 루프가 MQTT 없어도 동작해야 한다.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import paho.mqtt.client as mqtt


class MQTTPublisher:
    """단방향 publish 전용 MQTT 클라이언트 래퍼."""

    def __init__(
        self,
        host: str,
        port: int,
        client_id: str,
        keepalive: int = 60,
    ) -> None:
        self.host = host
        self.port = port
        self.client_id = client_id
        self.keepalive = keepalive
        self._connected = False

        self._client = mqtt.Client(client_id=client_id)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

        try:
            self._client.connect(host, port, keepalive)
            self._client.loop_start()
        except Exception as e:
            print(f"[mqtt] connect failed ({host}:{port}): {e} — running in no-op mode")

    # ---- 콜백 -------------------------------------------------------------
    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            self._connected = True
            print(f"[mqtt] connected to {self.host}:{self.port}")
        else:
            print(f"[mqtt] connect rc={rc}")

    def _on_disconnect(self, client, userdata, rc) -> None:
        self._connected = False
        if rc != 0:
            print(f"[mqtt] unexpected disconnect rc={rc}")

    # ---- 발행 -------------------------------------------------------------
    def publish_granted(self, user: str, confidence: float) -> None:
        self._publish_json(
            "dualguard/access/granted",
            {
                "time": _now_iso(),
                "user": user,
                "confidence": round(confidence, 4),
            },
        )

    def publish_denied(self, reason: str, confidence: float,
                       user: Optional[str] = None) -> None:
        payload = {
            "time": _now_iso(),
            "reason": reason,
            "confidence": round(confidence, 4),
        }
        if user:
            payload["user"] = user
        self._publish_json("dualguard/access/denied", payload)

    def publish_status(self, status: str) -> None:
        self._publish_json(
            "dualguard/system/status",
            {"time": _now_iso(), "status": status},
        )

    def close(self) -> None:
        try:
            self.publish_status("stopped")
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:
            pass

    # ---- 내부 -------------------------------------------------------------
    def _publish_json(self, topic: str, payload: dict,
                      qos: int = 0, retain: bool = False) -> None:
        try:
            self._client.publish(topic, json.dumps(payload), qos=qos, retain=retain)
        except Exception as e:
            print(f"[mqtt] publish failed ({topic}): {e}")


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
