"""MQTT → Telegram 브릿지 (명세서 F4 보강).

별도 프로세스로 동작. Mosquitto 브로커의 ``dualguard/#`` 토픽을 구독하여
텔레그램 봇 API로 사용자에게 푸시 알림을 전달한다.

main.py와 분리되어 있어 텔레그램 API 장애가 인증 시스템에 영향 주지 않는다.

실행:
    python telegram_bridge.py

환경변수 (DualGuard/.env):
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import paho.mqtt.client as mqtt
import requests
from dotenv import load_dotenv

import config

load_dotenv(Path(__file__).resolve().parent / ".env")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TOPIC_FILTER = "dualguard/#"


def send_telegram(text: str) -> None:
    """텔레그램 sendMessage API 호출."""
    if not BOT_TOKEN or not CHAT_ID:
        print("[bridge] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing in .env")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=5)
        if r.status_code != 200:
            print(f"[bridge] telegram error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"[bridge] telegram request failed: {e}")


def format_message(topic: str, payload: dict) -> str:
    """토픽별 텔레그램 메시지 포맷."""
    t = payload.get("time", "?")
    if topic.endswith("/granted"):
        user = payload.get("user", "?")
        conf = payload.get("confidence", 0)
        return f"[OK] {user} entered  (conf={conf})\n{t}"
    if topic.endswith("/denied"):
        reason = payload.get("reason", "?")
        conf = payload.get("confidence", 0)
        user = payload.get("user")
        who = f" user={user}" if user else ""
        return f"[DENY] {reason}{who}  (conf={conf})\n{t}"
    if topic.endswith("/status"):
        return f"[SYS] DualGuard {payload.get('status', '?')}  {t}"
    return f"{topic}: {payload}"


def on_connect(client, userdata, flags, rc) -> None:
    if rc == 0:
        print(f"[bridge] connected, subscribing {TOPIC_FILTER}")
        client.subscribe(TOPIC_FILTER)
    else:
        print(f"[bridge] connect rc={rc}")


def on_message(client, userdata, msg) -> None:
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception:
        payload = {"raw": msg.payload.decode("utf-8", errors="replace")}

    text = format_message(msg.topic, payload)
    print(f"[bridge] {msg.topic} -> {text}")
    send_telegram(text)


def main() -> None:
    if not BOT_TOKEN or not CHAT_ID:
        print(
            "[bridge] missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID. "
            "Copy .env.example to .env and fill in values.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = mqtt.Client(client_id="dualguard-telegram-bridge")
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[bridge] connecting {config.MQTT_BROKER_HOST}:{config.MQTT_BROKER_PORT}")
    client.connect(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT,
                   config.MQTT_KEEPALIVE)

    send_telegram("[SYS] telegram bridge started")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[bridge] stopping")
        send_telegram("[SYS] telegram bridge stopped")
        client.disconnect()


if __name__ == "__main__":
    main()
