"""DualGuard 전역 설정값.

명세서 4.1, 5.2 기반의 GPIO 핀 매핑, AI 임계값, 경로, MQTT 토픽 등
런타임 동작에 필요한 상수를 한 곳에 모아둔다.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# 경로
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

USERS_JSON = DATA_DIR / "users.json"
EMBEDDINGS_NPY = DATA_DIR / "embeddings.npy"
ACCESS_LOG_CSV = DATA_DIR / "access_log.csv"
ATTACK_SAMPLES_DIR = DATA_DIR / "attack_samples"

FACENET_WEIGHTS = MODELS_DIR / "facenet.pt"
MINIFASNET_WEIGHTS = MODELS_DIR / "mini_fasnet.pth"

# ---------------------------------------------------------------------------
# 카메라
# ---------------------------------------------------------------------------
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
TARGET_FPS = 15

# ---------------------------------------------------------------------------
# AI 임계값 (명세서 F2, F5)
# ---------------------------------------------------------------------------
FACENET_SIM_THRESHOLD = 0.7      # 코사인 유사도 최소값
FASNET_REAL_THRESHOLD = 0.5      # Real 신뢰도 최소값

# 융합 알고리즘
FUSION_MODE = "AND"              # "AND" | "WEIGHTED"
FUSION_ALPHA = 0.6               # FaceNet 가중치
FUSION_BETA = 0.4                # MiniFASNet 가중치
FUSION_COMBINED_THRESHOLD = 0.65

# 등록 시 캡처 매수
REGISTER_NUM_SAMPLES = 8

# ---------------------------------------------------------------------------
# GPIO 핀 매핑 (명세서 5.2, BCM 기준)
# ---------------------------------------------------------------------------
PIN_SERVO = 18           # PWM
PIN_LED_GREEN = 23
PIN_LED_RED = 24
PIN_BUZZER = 25
# LCD I2C: SDA=GPIO2, SCL=GPIO3 (전용 핀)
LCD_I2C_ADDRESS = 0x27
LCD_COLS = 16
LCD_ROWS = 2

# 서보 각도
SERVO_ANGLE_CLOSED = 0
SERVO_ANGLE_OPEN = 90
DOOR_OPEN_DURATION_SEC = 3.0

# LED/부저 동작
RED_BLINK_COUNT = 3
RED_BLINK_INTERVAL_SEC = 1.0
BUZZER_DENY_BEEPS = 3

# ---------------------------------------------------------------------------
# MQTT (명세서 F4)
# ---------------------------------------------------------------------------
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_CLIENT_ID = "dualguard-pi"

TOPIC_ACCESS_GRANTED = "dualguard/access/granted"
TOPIC_ACCESS_DENIED = "dualguard/access/denied"
TOPIC_SYSTEM_STATUS = "dualguard/system/status"

# ---------------------------------------------------------------------------
# 로그
# ---------------------------------------------------------------------------
LOG_CSV_HEADER = [
    "timestamp", "user", "result", "reason",
    "facenet_score", "fasnet_score",
]
