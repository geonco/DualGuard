# MQTT 통신 구조 (DualGuard)

> 보고서 / PPT 작성 시 참고용 메모. 명세서 F4(MQTT 통신 기능) 보강.

## 1. MQTT 한 줄 요약

**Publisher가 메시지를 직접 받는 사람에게 보내지 않고, 중간의 Broker(우체국)에 토픽(주소)을 붙여 던져두면, 그 토픽을 구독한 Subscriber가 알아서 가져가는 Pub/Sub 프로토콜.**

발신자와 수신자가 서로의 존재를 몰라도 되는 **느슨한 결합(loosely coupled)** 구조라, IoT 시스템에서 표준처럼 쓰인다.

## 2. 전체 흐름도

```
┌──────────────────┐                                      ┌──────────────────┐
│  Pi (DualGuard)  │                                      │  Subscriber #1   │
│   = Publisher    │                                      │  텔레그램 브릿지 │
│                  │  publish                  subscribe  │                  │
│  "임건우 통과!"  │ ───────┐               ┌─────────── │  토픽 듣다가     │
└──────────────────┘        │               │            │  텔레그램 발송   │
                            ▼               │            └──────────────────┘
                     ┌─────────────────────────┐
                     │   Mosquitto Broker      │  ← 우체국 본체
                     │   (Pi의 localhost:1883) │     메시지를 받아서
                     │                         │     구독자에게 뿌려줌
                     │   토픽 게시판:          │
                     │   - dualguard/access/granted │
                     │   - dualguard/access/denied  │
                     │   - dualguard/system/status  │
                     └─────────────────────────┘
                            ▲               │
                            │               │            ┌──────────────────┐
                            │               └──────────► │  Subscriber #2   │
                            │                            │  mosquitto_sub   │
                            │                            │  (시연 모니터링) │
                            │                            └──────────────────┘
                            │
                            │                            ┌──────────────────┐
                            └─────────────────────────── │  Subscriber #3   │
                                                         │  (확장 여지)     │
                                                         └──────────────────┘
```

## 3. 핵심 개념 3가지

| 개념 | 설명 | DualGuard에서 |
|------|------|---------------|
| **Broker** | 메시지를 중계하는 서버. Publisher와 Subscriber 어느 쪽도 서로를 직접 모름 | Pi에 설치한 Mosquitto, `localhost:1883` |
| **Topic** | 메시지에 붙는 계층적 주소. `/`로 구분, `#` 와일드카드 지원 | `dualguard/access/granted` 등 3종 |
| **Publish / Subscribe** | 발행자는 토픽에 메시지를 던지고, 구독자는 관심 토픽만 골라 받음 | Pi가 publish, 텔레그램 브릿지·`mosquitto_sub`가 subscribe |

## 4. DualGuard에서 메시지 흐름

```
[얼굴 인증 통과]
      │
      ▼
main.py:
  mqtt_publisher.publish_granted("임건우", 0.85)
      │
      ▼ TCP / 포트 1883
  Mosquitto Broker (Pi 내부)
      │
      │  "dualguard/access/granted" 구독자 전부에게 복사 전송
      │
      ├──► mosquitto_sub  ─→  발표용 터미널 화면
      │
      └──► telegram_bridge.py  ─→  텔레그램 봇 API  ─→  사용자 휴대폰 알림
```

## 5. 토픽 설계 (명세서 F4)

| 토픽 | 발행 시점 | Payload (JSON) |
|------|-----------|----------------|
| `dualguard/access/granted` | 인증 통과 | `{"time", "user", "confidence"}` |
| `dualguard/access/denied`  | 차단 (Unknown / Spoof) | `{"time", "reason", "confidence"}` |
| `dualguard/system/status`  | 프로세스 시작·종료 | `{"time", "status"}` |

## 6. 직접 텔레그램 호출 대신 MQTT를 끼는 이유

| 이점 | 설명 |
|------|------|
| **확장성** | 나중에 슬랙·웹 대시보드·다른 Pi가 추가돼도 `main.py`는 손대지 않음. Subscriber만 새로 붙이면 됨 |
| **장애 격리** | 텔레그램 API가 다운돼도 인증 시스템은 정상 동작. 브릿지만 영향받음 |
| **표준 프로토콜** | "IoT 통신 사용" 가이드라인 충족 (명세서 1.3) |
| **보고서 가치** | Pub/Sub 분산 아키텍처로 설명 가능 — 단일 책임 / 모듈 분리 강조 |

## 7. 우리가 구현할 것

- `modules/mqtt_publisher.py` : Pi 측 발행자 (paho-mqtt)
- `telegram_bridge.py` (신규) : 별도 프로세스. MQTT 구독 → 텔레그램 봇 API로 포워딩
- Mosquitto 브로커 설치 (`sudo apt install mosquitto mosquitto-clients`)

## 8. 시연 시 모니터링 명령

```bash
# 모든 DualGuard 토픽 실시간 출력
mosquitto_sub -h localhost -t "dualguard/#" -v
```

발표 화면에 이 터미널을 띄워두면 인증 이벤트가 JSON으로 흐르는 게 시각적으로 보여 IoT 통신을 입증하기 좋다.
