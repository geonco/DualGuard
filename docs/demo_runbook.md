# DualGuard 시연 런북

발표 당일 Pi에서 그대로 복붙하는 용. 평가용 5종 공격 측정 절차도 포함.

배선은 `docs/wiring.md` 참조 — 여기서는 코드를 어떻게 돌리는지만 다룸.

---

## 0. 발표 전날·당일 사전 점검

```bash
cd ~/DualGuard
git pull
source .venv/bin/activate
pip install -r requirements.txt
pip install RPi.GPIO RPLCD smbus2    # 처음 한 번만

# .env에 텔레그램 토큰 있는지
cat .env
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHAT_ID=...

# Mosquitto active 인지
sudo systemctl status mosquitto
sudo systemctl start mosquitto       # 안 켜져있으면

# 카메라
ls /dev/video*                       # /dev/video0 보여야 됨

# I2C / LCD
sudo i2cdetect -y 1                  # 0x27 (또는 0x3f) 보여야 됨

# 등록된 사용자 확인
cat data/users.json
```

### 하드웨어 smoke test (5종 부품 한방에)

```bash
python -c "from modules.gpio_controller import GPIOController; import time; \
g = GPIOController(); time.sleep(1); \
g.set_led('green', True); time.sleep(0.5); g.set_led('green', False); \
g.set_led('red', True); time.sleep(0.5); g.set_led('red', False); \
g.beep(2); g.open_door(); g.cleanup()"
```

기대: LCD `DualGuard / Ready` → 초록 0.5s → 빨강 0.5s → 비프 2회 → 서보 90° → 복귀.

---

## 1. 시연 직전 — 터미널 3개 띄우기

> tmux 쓰면 한 화면에서 분할 가능. 안 쓰면 LXTerminal 3개.

### 터미널 ① — MQTT 모니터 (발표 화면에 띄울 것)
```bash
mosquitto_sub -h localhost -t "dualguard/#" -v
```
> 인증 이벤트가 JSON으로 흐름. IoT 통신 입증용.

### 터미널 ② — 텔레그램 브릿지
```bash
cd ~/DualGuard && source .venv/bin/activate
python telegram_bridge.py
```
> 폰에 `[SYS] telegram bridge started` 오면 OK. 멈추지 않는 게 정상.

### 터미널 ③ — 메인 인증 루프
```bash
cd ~/DualGuard && source .venv/bin/activate
python main.py                       # 기본 (config.FUSION_MODE = AND)
# 또는
python main.py --mode WEIGHTED       # 가중 융합으로 시작
python main.py --no-preview          # SSH/PuTTY에서 헤드리스
```
> 카메라 미리보기 창. 종료는 창에서 `q` 또는 `Ctrl+C`.

---

## 2. 시연 시나리오 (명세서 §10, 약 2분 30초)

| # | 동작 | 기대 결과 |
|---|------|-----------|
| ① 정상 통과 | 발표자가 카메라 앞 | LCD `Access granted / Hi {name}`, 서보 90°, 초록 LED, 비프 1회, 텔레그램 `[OK] {name} entered` |
| ② 사진 공격 | 핸드폰 사진 들이댐 | LCD `Access denied / SpoofDetected`, 빨강 LED 3회 점멸, 비프 3회, 텔레그램 `[DENY] SpoofDetected` |
| ③ 영상 공격 | 노트북 영상 재생 | 동일하게 차단 |
| ④ 미등록자 | 청중 한 명 카메라 앞 | LCD `Access denied / UnknownUser`, 텔레그램 `[DENY] UnknownUser` |
| ⑤ 팀원 통과 | Member B 카메라 앞 | 정상 통과 (재현성 입증) |

> 차단 사유 우선순위: `UnknownUser` > `SpoofDetected`. 즉 미등록자가 사진을 들이대도 사유는 `UnknownUser`로 찍힘.

---

## 3. 사용자 등록 (시연 전 미리)

```bash
python register.py --name 임건우
```
> 8장 자동 캡처. 동명이인이면 `_2`, `_3` 자동 suffix. 캡처 사진은 `data/registered_samples/<name>/`에서 검토 가능.

---

## 4. 5종 공격 평가 — 보고서 표 1·표 2 데이터 산출

명세서 9.1 평가. 각 시나리오 **10회**씩 시도, **두 융합 모드** 모두.

### 측정 절차

```bash
# 한 모드에서 다 돌리고 → CSV 백업 → 모드 바꿔 다시
python main.py --mode AND
# 5종 × 10회 = 50회 시도 후 Ctrl+C

cp data/access_log.csv data/access_log_AND.csv

python main.py --mode WEIGHTED
# 다시 5종 × 10회 = 50회
cp data/access_log.csv data/access_log_WEIGHTED.csv
```

### 5종 공격

| 공격 | 준비물 | 비고 |
|---|---|---|
| Print Attack | A4 본인 얼굴 인쇄물 | 컬러 인쇄, 실제 크기 |
| Phone Display - 정지 사진 | 폰 갤러리에서 본인 사진 띄움 | 밝기 최대 |
| Phone Display - 동영상 | 본인 셀카 영상 재생 | 자연스러운 표정 변화 |
| Laptop Display | 노트북 풀스크린 사진/영상 | 광택·반사 영향 |
| Paper Mask | A4 마스크 (눈·입 구멍) | 얼굴 앞에 들기 |

### CSV → 표 만들기

`data/access_log.csv` 컬럼: `timestamp, user, result, reason, facenet_score, fasnet_score`

각 공격당 차단율(=`reason=SpoofDetected`/시도 횟수)을 계산. AND vs WEIGHTED 두 모드 결과를 표 1로 비교, 정상 통과 false reject율을 표 2로.

---

## 5. 종료 순서

```bash
# 터미널 ③ main.py: 미리보기에서 q 또는 Ctrl+C
# 터미널 ② telegram_bridge.py: Ctrl+C
# 터미널 ① mosquitto_sub: Ctrl+C
# Mosquitto 브로커는 systemd가 관리 — 그대로 둬도 됨
```

`main.py`가 정상 종료되면 `gpio.cleanup()`이 LCD clear + 서보 stop + LED/부저 LOW + `GPIO.cleanup()` 호출. 강제 종료(`kill -9`)는 GPIO 상태 남을 수 있으니 피하기.

---

## 6. Plan B — 시연 실패 시

ZIP 제출물에 포함된 사전 녹화 데모 영상을 노트북에서 재생. (과제 가이드라인 명시: 현장 실패 시 백업 영상 필수)

---

## 7. 트러블슈팅 핫픽스

| 증상 | 즉시 대응 |
|---|---|
| 카메라 안 잡힘 | USB 재연결 → `ls /dev/video*` 재확인 → `main.py` 재실행 |
| 텔레그램 알림 안 옴 | 터미널 ②에 `connected` 떴는지 → `.env` 토큰 → Wi-Fi → `mosquitto_sub`에 메시지 흐르는지 |
| MQTT 안 흐름 | `sudo systemctl restart mosquitto` |
| LCD 글자 안 보임 | 백팩 뒤 파란 가변저항으로 명암 조정 / `i2cdetect -y 1`로 주소 재확인 (다르면 `config.py` 수정) |
| 서보 움직일 때 Pi 리부팅 | 외부 5V로 서보 VCC만 분리, GND는 Pi와 공통 |
| 부저가 LOW 상태에서도 울음 | 극성 반대 — (+)(-)단자 바꿔 꽂기 |
| FPS 너무 낮음 | 다른 창 닫기, `--no-preview` 헤드리스 |
| 인식률 낮음 | 조명 밝게, 카메라 30~60cm |
| 다 막혔을 때 | 백업 영상 (§6) |

---

## 8. 평가표·발표용 산출물 체크리스트

- [ ] `data/access_log_AND.csv`, `data/access_log_WEIGHTED.csv` (5×10×2=100회 기록)
- [ ] 표 1 (5종 공격 × 2 모드 차단율) → 보고서·PPT
- [ ] 표 2 (정상 통과 false reject율, 평균 인증 시간) → 보고서·PPT
- [ ] 데모 영상 (5종 시나리오 전부) — 사전 녹화
- [ ] 보고서 PDF (≥10페이지)
- [ ] PPT (영문, ≥15슬라이드, 8분+Q&A 2분)
- [ ] `IoT_YourName_StudentID_TermProject.rar` 압축 제출 (6/22)
