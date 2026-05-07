# 🛡 DualGuard

**Edge AI Face Recognition and Anti-Spoofing Access Control System on Raspberry Pi**
IoT Term Project — Spring 2026, HUFS Computer Engineering

---

## 프로젝트 소개

카메라가 비추는 얼굴이 (1) 등록된 사용자인지(Face Recognition), (2) 진짜 사람인지(Anti-Spoofing)를 두 개의 독립적인 AI 모델로 검증하는 **이중 검증(Dual Verification)** 출입 시스템.

- **Stage 0 (Detection)** — MediaPipe로 얼굴 영역 추출
- **Stage 1 (Recognition)** — FaceNet(InceptionResNetV1)으로 등록자 식별
- **Stage 2 (Anti-Spoofing)** — MiniFASNet(V1SE+V2 앙상블)으로 사진/영상/마스크 공격 차단

두 검증을 모두 통과해야 서보모터가 회전하여 문이 열리며, 모든 출입 이벤트는 MQTT로 발행되고 CSV 로그로 영구 보관된다.

---

## 디렉토리 구조

```
DualGuard/
├── main.py                # 실시간 인증 루프
├── register.py            # 신규 사용자 등록
├── config.py              # 설정값 (임계값, GPIO, 경로)
├── demo_detector.py       # Stage 0 단독 데모
├── demo_recognizer.py     # Stage 1 단독 데모
├── demo_anti_spoof.py     # Stage 2 단독 데모
├── modules/
│   ├── face_detector.py
│   ├── face_recognizer.py
│   ├── anti_spoofing.py
│   ├── fusion.py
│   ├── gpio_controller.py     # (Member B 영역, 미구현)
│   ├── mqtt_publisher.py      # (Member B 영역, 미구현)
│   └── data_manager.py
├── data/                  # users.json, embeddings.npy, access_log.csv (gitignore)
├── tests/
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

## 셋업 — Pi에서 처음부터

### 0. Python 버전 먼저 확인

```bash
python3 --version
```

**Python 3.9~3.11 필요.** mediapipe가 3.12+ aarch64 휠을 제공하지 않는다. Pi OS Trixie 등 최신 OS는 기본이 3.13이므로 **반드시 3.11로 다운그레이드**해야 한다.

3.11이 아닌 경우 pyenv로 설치:

```bash
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
  libreadline-dev libsqlite3-dev curl git libncursesw5-dev xz-utils tk-dev \
  libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

curl https://pyenv.run | bash

cat >> ~/.bashrc <<'EOF'
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF
exec bash

pyenv install 3.11.9   # 소스 빌드, Pi에서 10~20분
```

### 1. 저장소 클론

```bash
cd ~
git clone <repo-url> DualGuard
cd DualGuard
pyenv local 3.11.9   # Python 3.11 미만이면 생략
```

### 2. 가상환경 + 의존성

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

**먼저 CPU 전용 torch 설치 (NVIDIA CUDA 라이브러리 다운 방지, 수 GB 절약):**

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

그 다음 나머지:

```bash
pip install -r requirements.txt
```

mediapipe + facenet-pytorch + opencv 등 합쳐 ~1GB, 15~30분 소요.

### 3. 카메라 인식 확인

USB 웹캠 꽂고:

```bash
ls /dev/video*    # /dev/video0 보이면 OK
```

빠른 테스트 (VNC 환경에서):

```bash
python demo_detector.py
```

얼굴 비추면 초록 박스 + FPS 표시되면 카메라/MediaPipe 셋업 완료.

### 4. 사용자 등록 — **여기까지 하면 본인 등록 가능**

```bash
python register.py --name <your_name>
```

8장 자동 캡처 후 `data/users.json` + `data/embeddings.npy` 생성. 캡처된 얼굴 사진은 `data/registered_samples/<name>/01.jpg ~ 08.jpg`로 저장돼 검토 가능.

> **여기까지가 등록자 본인 작업의 끝.** 아래 5단계는 main.py로 인증 루프 돌릴 때만 필요.

### 5. (선택) Anti-Spoofing 셋업 — main.py 실행 시 필요

`anti_spoofing.py`는 [Silent-Face-Anti-Spoofing](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing) 저장소의 모델 정의 + 가중치를 사용한다.

```bash
cd ~
git clone https://github.com/minivision-ai/Silent-Face-Anti-Spoofing.git
```

기본 경로는 `~/Silent-Face-Anti-Spoofing`. 다른 위치에 두려면 `SILENT_FACE_ROOT` 환경변수로 지정:

```bash
export SILENT_FACE_ROOT=/path/to/Silent-Face-Anti-Spoofing
```

가중치(`resources/anti_spoof_models/*.pth`)는 그 저장소 안에 이미 포함되어 있어 별도 다운로드 불필요.

### 6. (선택) Mosquitto + I2C — 하드웨어 통합 시 필요

```bash
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto

sudo raspi-config       # Interface Options → I2C → Enable
```

---

## 사용법

### 단독 데모 (각 스테이지 단독 검증)

```bash
python demo_detector.py     # MediaPipe 얼굴 검출만
python demo_recognizer.py   # 검출 + FaceNet 인식
python demo_anti_spoof.py   # 검출 + MiniFASNet
```

### 전체 인증 루프

```bash
python main.py                  # 기본 (config.FUSION_MODE)
python main.py --mode AND       # 단순 AND 결합
python main.py --mode WEIGHTED  # 가중 융합 (α=0.6, β=0.4)
python main.py --no-preview     # 미리보기 창 없이 (PuTTY/SSH용)
```

종료: 미리보기 창에서 `q`, 또는 터미널에서 `Ctrl+C`.

### MQTT 모니터링 (하드웨어 통합 후)

```bash
mosquitto_sub -h localhost -t "dualguard/#" -v
```

### 단위테스트

```bash
python -m pytest tests/ -v
```

---

## 평가 시나리오

5종 공격에 대해 각 10회 시도하여 차단율 측정:

1. Print Attack (A4 인쇄물)
2. Phone Display — 정지 사진
3. Phone Display — 동영상
4. Laptop Display
5. Paper Mask

자세한 평가 계획과 융합 알고리즘 비교(AND vs 가중)는 명세서 9절 참조.

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `ERROR: No matching distribution found for mediapipe` | Python 3.12+ — pyenv로 3.11.9 설치 후 venv 재생성 |
| 설치 중 `nvidia-*` 패키지가 GB 단위로 다운로드됨 | torch 기본 휠이 CUDA 포함. CPU torch 먼저 설치 (셋업 2단계) |
| `cv2.error: ... Can't open "./resources/detection_model/deploy.prototxt"` | Silent-Face 저장소를 `~/Silent-Face-Anti-Spoofing`에 두지 않음. clone 위치 확인 또는 `SILENT_FACE_ROOT` 환경변수 |
| 카메라 안 잡힘 (`/dev/video0` 없음) | USB 케이블 재연결, `lsusb`로 인식 여부 확인 |
| fswebcam 사진이 어두움 | `fswebcam -S 20` 으로 워밍업 프레임 스킵. OpenCV는 영향 없음. |

---

## 라이선스 / 참조

- [Silent-Face-Anti-Spoofing](https://github.com/minivision-ai/Silent-Face-Anti-Spoofing) — minivision-ai
- [facenet-pytorch](https://github.com/timesler/facenet-pytorch) — timesler
- [MediaPipe](https://google.github.io/mediapipe/) — Google
- [paho-mqtt](https://www.eclipse.org/paho/) — Eclipse
