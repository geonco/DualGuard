# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 상태

현재 **뼈대만 있는 상태**다. 모든 모듈은 docstring + 함수 시그니처 + `TODO`/`raise NotImplementedError` 만 채워져 있고, 실제 추론·GPIO·MQTT 코드는 비어 있다. 새 기능을 짤 때는 `명세서 → config.py 상수 → 해당 모듈 구현` 순으로 내려가면서 TODO를 채우는 흐름이다.

명세서 원본(상세 기능 요구, 평가 시나리오, GPIO 핀맵, 데이터 스키마)은 저장소 루트가 아니라 한 단계 위 `../DualGuard_명세서.md.pdf` 에 있다. 작업 시 거의 항상 참조해야 한다.

## 자주 쓰는 명령

```bash
# 가상환경 + 의존성 (Pi에서)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 사용자 등록 (F1) — 카메라로 5~10장 자동 캡처
python register.py

# 실시간 인증 루프 (F2)
python main.py

# MQTT 모니터링 — 발표/디버그용
mosquitto_sub -h localhost -t "dualguard/#" -v

# 단일 테스트 실행 (tests/ 채워진 후)
pytest tests/test_xxx.py::test_yyy -v
```

`requirements.txt` 의 `RPi.GPIO`, `gpiozero`, `smbus2`, `RPLCD` 는 `platform_machine` marker로 ARM 플랫폼 한정이다. Windows/macOS 개발 머신에서는 `pip install -r requirements.txt` 가 자동으로 스킵하므로 별도 처리 불필요. 단, `gpio_controller.py` 와 `register.py`/`main.py` 는 Pi에서만 끝까지 돌아간다.

## 아키텍처 핵심

### 3단계 파이프라인 (반드시 이 순서)

```
Camera frame
  → FaceDetector (MediaPipe)        # Stage 0: bbox 없으면 즉시 다음 프레임
  → FaceRecognizer (FaceNet)        # Stage 1: 512-d 임베딩 + 코사인 유사도
  → AntiSpoofing (MiniFASNet)       # Stage 2: Real/Spoof 확률
  → fusion.decide_*()               # AND 또는 가중 융합
  → GPIOController + MQTTPublisher + DataManager  # 부수효과
```

Stage 1에서 Unknown이 나와도 Stage 2까지 돌려서 **두 점수를 모두 로그/MQTT에 기록**해야 한다 (평가 표 9.3에 single-vs-dual 비교가 들어가기 때문). 단 차단 사유는 가장 먼저 실패한 단계로 결정된다 (`UnknownUser` 가 `SpoofDetected` 보다 우선).

### 융합 알고리즘은 두 방식을 **둘 다** 구현한다

`fusion.py` 의 `decide_and` 와 `decide_weighted` 둘 다 보고서 핵심 비교 결과(표 1)에 들어간다. 한쪽만 구현하면 안 된다. `config.FUSION_MODE` 로 런타임 전환한다.

### config.py 가 단일 진실 공급원

GPIO 핀, AI 임계값, 융합 파라미터, MQTT 토픽, 파일 경로가 전부 `config.py` 에 있다. 매직 넘버를 모듈 안에 박지 말고 항상 `config.XXX` 로 참조해서 환경별 튜닝을 한 파일에서 끝내야 한다 (명세서 11. 리스크 대응 — "임계값 환경별 튜닝"이 항목으로 잡혀 있다).

### 데이터 영속성: 두 파일이 한 쌍

`data/users.json` 의 `embedding_index` 가 `data/embeddings.npy` 의 행 번호와 1:1 매핑된다. 이 두 파일은 **항상 같이 쓰고 같이 읽어야** 한다 — 한쪽만 갱신하면 인덱스가 어긋나서 다른 사람으로 인식된다. 모든 입출력은 `DataManager` 를 통해서만 한다 (직접 `np.load` / `json.load` 금지).

`access_log.csv` 헤더는 `config.LOG_CSV_HEADER` 가 권위 있는 정의다. 컬럼 순서 변경 시 평가 스크립트도 같이 손봐야 한다.

### 이름 충돌(동명이인)

`F1` 명세대로 `DataManager.resolve_unique_name("임건우")` 가 이미 있으면 `임건우_2`, `임건우_3` ... 식으로 suffix 부여한다. `register.py` 는 반드시 이 헬퍼를 거쳐서 `add_user` 를 호출해야 한다.

## 개발 워크플로

- 메인 브랜치: `main`. 작업 브랜치: `geonwoo_branch` (Member A — AI/Software). Member B는 별도 브랜치를 가질 예정이라, 모듈을 수정할 때 충돌 가능성을 의식한다 (특히 `gpio_controller.py`, `mqtt_publisher.py` 는 Member B 영역).
- 빈 디렉토리(`data/`, `models/`, `tests/`, `docs/`)는 `.gitkeep` 으로만 추적되고 있다. 실제 파일 추가 시 `.gitkeep` 은 그대로 두면 된다.
- 모델 가중치는 git에 올리지 않는다 (용량). `models/facenet.pt` 는 facenet-pytorch가 첫 실행 시 자동 다운로드, `models/mini_fasnet.pth` 는 Silent-Face-Anti-Spoofing 저장소에서 수동 배치.

## 평가 / 시연 제약

- 인증 1회 ≤ **0.5~1초**, 미리보기 ≥ **15 FPS** (명세서 F2 성능 목표). 새 기능이 이 예산을 깎으면 안 된다.
- 평가는 명세서 9.1의 5종 공격(Print / Phone-사진 / Phone-영상 / Laptop / Paper Mask)에 대해 각 10회씩, 결과는 표 1·표 2 양식 그대로 보고서에 들어간다. 새 임계값/파라미터를 바꿨을 땐 이 표를 재생성할 수 있는지 항상 의식한다.
- 시연 장애 대비 백업 영상이 필수 산출물이라 — 동작 변경 시 시연 시나리오 5종(통과 / 사진공격 / 영상공격 / 미등록자 / 팀원 통과)이 깨지지 않는지 확인.
