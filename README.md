# 🛡 DualGuard

**Edge AI Face Recognition and Anti-Spoofing Access Control System on Raspberry Pi**
IoT Term Project — Spring 2026, HUFS Computer Engineering

---

## 프로젝트 소개

카메라가 비추는 얼굴이 (1) 등록된 사용자인지(Face Recognition), (2) 진짜 사람인지(Anti-Spoofing)를 두 개의 독립적인 AI 모델로 검증하는 **이중 검증(Dual Verification)** 출입 시스템.

- **Stage 0 (Detection)** — MediaPipe로 얼굴 영역 추출
- **Stage 1 (Recognition)** — FaceNet(InceptionResNetV1)으로 등록자 식별
- **Stage 2 (Anti-Spoofing)** — MiniFASNet으로 사진/영상/마스크 공격 차단

두 검증을 모두 통과해야 서보모터가 회전하여 문이 열리며, 모든 출입 이벤트는 MQTT로 발행되고 CSV 로그로 영구 보관된다.

---

## 디렉토리 구조

```
DualGuard/
├── main.py                # 실시간 인증 루프
├── register.py            # 신규 사용자 등록
├── config.py              # 설정값 (임계값, GPIO, 경로)
├── modules/
│   ├── face_detector.py
│   ├── face_recognizer.py
│   ├── anti_spoofing.py
│   ├── fusion.py
│   ├── gpio_controller.py
│   ├── mqtt_publisher.py
│   └── data_manager.py
├── models/                # 사전학습 가중치
├── data/                  # users.json, embeddings.npy, access_log.csv
├── tests/
├── docs/
└── requirements.txt
```

---

## 하드웨어 요구사항

- Raspberry Pi 4B (8GB), 64-bit Raspberry Pi OS
- USB 웹캠 (예: 로지텍 C270)
- SG90 서보모터, 빨강/초록 LED + 220Ω 저항, 능동 부저, LCD 1602 (I2C)
- 점퍼 와이어, 브레드보드, 도어 모형(마분지/폼보드)

GPIO 핀 매핑은 `config.py` 참조 (서보 GPIO18, 초록 LED GPIO23, 빨강 LED GPIO24, 부저 GPIO25, LCD I2C SDA/SCL).

---

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repo-url> DualGuard
cd DualGuard
```

### 2. Python 가상환경 (Pi에서)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Mosquitto 브로커 설치 (Pi)

```bash
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
```

### 4. I2C 활성화 (LCD용)

```bash
sudo raspi-config   # Interface Options → I2C → Enable
```

### 5. 모델 가중치 배치

- FaceNet: `facenet-pytorch`가 최초 실행 시 자동 다운로드
- MiniFASNet: [Silent-Face-Anti-Spoofing](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing) 에서 받아 `models/mini_fasnet.pth`로 저장

---

## 사용법

### 사용자 등록

```bash
python register.py
```

이름 입력 → 카메라 앞에서 다양한 각도로 자동 캡처(5~10장) → `data/users.json` 및 `data/embeddings.npy` 갱신.

### 실시간 인증 실행

```bash
python main.py
```

카메라 미리보기 창이 뜨고, 얼굴 검출 시 자동으로 3단계 검증을 수행한다.

### MQTT 모니터링 (선택)

```bash
mosquitto_sub -h localhost -t "dualguard/#" -v
```

---

## 평가 시나리오

5종 공격에 대해 각 10회 시도하여 차단율 측정:

1. Print Attack (A4 인쇄물)
2. Phone Display — 정지 사진
3. Phone Display — 동영상
4. Laptop Display
5. Paper Mask

자세한 평가 계획과 융합 알고리즘 비교(AND vs 가중)는 `docs/` 참조.

---

## 라이선스 / 참조

- Silent-Face-Anti-Spoofing — minivision-ai
- facenet-pytorch — timesler
- MediaPipe — Google
- paho-mqtt — Eclipse
