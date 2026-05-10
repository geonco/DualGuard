# DualGuard 시연 명령어 체크리스트

> 발표 당일 Pi에서 그대로 복붙해서 쓰는 용. 모든 작업은 **Pi에서 VNC 접속한 상태**로 진행.

---

## 0. 발표 30분 전 — 사전 점검

```bash
# Pi에서
cd ~/DualGuard
git pull                        # 최신 코드 받기
source .venv/bin/activate
pip install -r requirements.txt # 의존성 최신화

# .env 존재 확인 (텔레그램 토큰)
cat .env

# Mosquitto 브로커 상태 (active 여야 함)
sudo systemctl status mosquitto
# 안 떠 있으면:
sudo systemctl start mosquitto

# 카메라 인식 확인
ls /dev/video*
```

---

## 1. 시연 직전 — 터미널 4개 띄우기

> tmux 쓰면 한 화면에서 분할 가능. 안 쓰면 그냥 LXTerminal 4번 열기.

### 터미널 ① — MQTT 모니터 (발표 화면에 띄울 것)
```bash
mosquitto_sub -h localhost -t "dualguard/#" -v
```
> 인증 이벤트가 JSON으로 흐르는 게 보임. **교수님께 IoT 통신 입증용**.

### 터미널 ② — 텔레그램 브릿지
```bash
cd ~/DualGuard
source .venv/bin/activate
python telegram_bridge.py
```
> 폰에 "telegram bridge started" 알림 오면 OK. 멈추지 않는 게 정상.

### 터미널 ③ — 메인 인증 루프
```bash
cd ~/DualGuard
source .venv/bin/activate
python main.py
```
> 카메라 미리보기 창이 뜨고, 얼굴 인식 시작. 종료는 미리보기 창에서 `q` 또는 터미널에서 `Ctrl+C`.

### (선택) 터미널 ④ — 융합 모드 비교 시연
```bash
# AND 모드 (기본)
python main.py --mode AND

# 가중 융합 모드
python main.py --mode WEIGHTED
```

---

## 2. 시연 시나리오 (명세서 §10, 약 2분 30초)

| 순서 | 동작 | 기대 결과 |
|------|------|-----------|
| ① 정상 통과 | 발표자가 카메라 앞에 섬 | LCD "Welcome ...", 서보 회전, 초록 LED, 폰 알림 `[OK]` |
| ② 사진 공격 | 핸드폰 사진 보여줌 | "Spoof Detected", 빨간 LED, 부저, 폰 알림 `[DENY] SpoofDetected` |
| ③ 영상 공격 | 노트북에서 영상 재생 | 동일하게 차단 |
| ④ 미등록자 | 청중 한 명 카메라 앞에 | "Unknown User", 폰 알림 `[DENY] UnknownUser` |
| ⑤ 팀원 통과 | Member B 카메라 앞에 | 정상 통과 (재현성 입증) |

---

## 3. 사용자 등록 (시연 전 또는 별도 준비)

```bash
cd ~/DualGuard
source .venv/bin/activate
python register.py --name 임건우
```
> 카메라 앞에서 다양한 각도로 표정 바꿔주면 자동 캡처 8장 → DB 저장.

---

## 4. 종료 순서 (역순)

```bash
# 터미널 ③ main.py: 미리보기에서 q 또는 Ctrl+C
# 터미널 ② telegram_bridge.py: Ctrl+C
# 터미널 ① mosquitto_sub: Ctrl+C
# 브로커는 그냥 둬도 됨 (systemd가 관리)
```

---

## 5. 백업 영상 재생 (Plan B — 시연 실패 시)

ZIP 제출물에 포함된 미리 녹화한 데모 영상을 노트북에서 재생.

---

## 6. 트러블슈팅 핫픽스

| 증상 | 즉시 대응 |
|------|-----------|
| 카메라 안 잡힘 | USB 다시 꽂기 → `python main.py` 재실행 |
| 텔레그램 알림 안 옴 | 터미널 ② 로그 확인. `.env` 토큰 오타? Wi-Fi 끊김? |
| MQTT 메시지 안 흐름 | `sudo systemctl restart mosquitto` |
| FPS 너무 낮음 | 다른 창 닫기, `main.py --no-preview` 로 헤드리스 실행 |
| 인식률 낮음 | 조명 밝게, 카메라 30~60cm 거리 유지 |
| 다 막혔을 때 | 백업 영상 (5번) |
