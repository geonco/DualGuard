"""GPIO 액추에이터 통합 제어 (명세서 F3, 5.2).

서보모터(SG90), 초록/빨강 LED, 능동 부저, LCD 1602(I2C)를 한 클래스로 묶어
인증 결과에 따른 물리적 동작을 일괄 처리한다.
"""

from __future__ import annotations


class GPIOController:
    """모든 GPIO 출력 장치를 관리하는 컨트롤러."""

    def __init__(self) -> None:
        """핀 초기화 + LCD 핸들 오픈.

        TODO:
            - RPi.GPIO setmode(BCM)
            - 서보 PWM 객체 생성 (50Hz)
            - LED, 부저 OUT 설정
            - RPLCD/smbus2로 LCD 초기화
        """
        raise NotImplementedError

    # ---- 통합 시나리오 ----------------------------------------------------
    def grant_access(self, user_name: str) -> None:
        """통과 동작: 서보 회전 + 초록 LED + 부저 1회 + LCD Welcome. TODO."""
        raise NotImplementedError

    def deny_access(self, reason: str) -> None:
        """차단 동작: 빨간 LED 점멸 + 부저 3회 + LCD 메시지. TODO."""
        raise NotImplementedError

    # ---- 개별 제어 --------------------------------------------------------
    def open_door(self) -> None:
        """서보 90도 회전 → 대기 → 원위치. TODO."""
        raise NotImplementedError

    def set_led(self, color: str, on: bool) -> None:
        """color in {"green", "red"}. TODO."""
        raise NotImplementedError

    def blink_red(self, count: int, interval: float) -> None:
        """빨간 LED 점멸. TODO."""
        raise NotImplementedError

    def beep(self, count: int = 1) -> None:
        """부저 비프. TODO."""
        raise NotImplementedError

    def lcd_show(self, line1: str, line2: str = "") -> None:
        """LCD에 메시지 출력. TODO."""
        raise NotImplementedError

    def cleanup(self) -> None:
        """GPIO.cleanup() + LCD clear. TODO."""
        raise NotImplementedError
