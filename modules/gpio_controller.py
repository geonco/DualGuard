"""GPIO actuator controller (spec F3, 5.2).

Servo (SG90), green/red LEDs, active buzzer, and LCD 1602 (I2C) are all
managed by this single class so the auth loop only needs two calls:
``grant_access`` and ``deny_access``.

On non-Pi dev machines (Windows/macOS) ``RPi.GPIO`` / ``RPLCD`` import will
fail; in that case we silently fall back to a no-op stub so main.py can
still run for camera + AI testing without hardware.

Grant/deny actions are dispatched to a worker thread guarded by a lock so
that (a) the camera preview keeps drawing while the servo holds the door
open and (b) overlapping triggers serialize instead of fighting.
"""

from __future__ import annotations

import threading
import time

import config

try:
    import RPi.GPIO as GPIO
    from RPLCD.i2c import CharLCD
    _HW_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO = None  # type: ignore
    CharLCD = None  # type: ignore
    _HW_AVAILABLE = False


class GPIOController:
    """Unified controller for servo + LEDs + buzzer + LCD."""

    def __init__(self) -> None:
        self._hw = _HW_AVAILABLE
        self._lock = threading.Lock()
        self._servo = None
        self._lcd = None

        if not self._hw:
            print("[gpio] hardware libs unavailable - running in no-op mode")
            return

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(config.PIN_SERVO, GPIO.OUT)
        GPIO.setup(config.PIN_LED_GREEN, GPIO.OUT)
        GPIO.setup(config.PIN_LED_RED, GPIO.OUT)
        GPIO.setup(config.PIN_BUZZER, GPIO.OUT)
        GPIO.output(config.PIN_LED_GREEN, GPIO.LOW)
        GPIO.output(config.PIN_LED_RED, GPIO.LOW)
        GPIO.output(config.PIN_BUZZER, GPIO.LOW)

        # SG90 servo: 50 Hz PWM
        self._servo = GPIO.PWM(config.PIN_SERVO, 50)
        self._servo.start(self._angle_to_duty(config.SERVO_ANGLE_CLOSED))
        time.sleep(0.3)
        # Stop pulse after reaching closed pos — prevents jitter/heating
        self._servo.ChangeDutyCycle(0)

        try:
            self._lcd = CharLCD(
                i2c_expander="PCF8574",
                address=config.LCD_I2C_ADDRESS,
                port=1,
                cols=config.LCD_COLS,
                rows=config.LCD_ROWS,
                charmap="A02",
                auto_linebreaks=True,
            )
            self._lcd.clear()
            self._lcd_write("DualGuard", "Ready")
        except Exception as e:
            print(f"[gpio] LCD init failed: {e} - continuing without LCD")
            self._lcd = None

        print("[gpio] hardware initialized (servo/LED/buzzer/LCD)")

    @staticmethod
    def _angle_to_duty(angle: float) -> float:
        # SG90 mapping: 0deg ~ 2.5% duty, 180deg ~ 12.5% at 50 Hz
        return 2.5 + (angle / 180.0) * 10.0

    # ---- Integrated scenarios ---------------------------------------------
    def grant_access(self, user_name: str) -> None:
        """Green LED + 1 beep + servo open (3s) + LCD welcome. Non-blocking."""
        if not self._hw:
            return
        threading.Thread(
            target=self._grant_worker, args=(user_name,), daemon=True
        ).start()

    def deny_access(self, reason: str) -> None:
        """Red LED blink + 3 beeps + LCD denied msg. Non-blocking."""
        if not self._hw:
            return
        threading.Thread(
            target=self._deny_worker, args=(reason,), daemon=True
        ).start()

    def _grant_worker(self, user_name: str) -> None:
        with self._lock:
            self._lcd_write("Access granted", f"Hi {user_name}")
            self.set_led("green", True)
            self.beep(1)
            self.open_door()
            self.set_led("green", False)
            self._lcd_write("DualGuard", "Ready")

    def _deny_worker(self, reason: str) -> None:
        with self._lock:
            self._lcd_write("Access denied", reason)
            # Beep and blink in sequence — keeps timing predictable for demo
            self.beep(config.BUZZER_DENY_BEEPS)
            self.blink_red(config.RED_BLINK_COUNT, config.RED_BLINK_INTERVAL_SEC)
            self._lcd_write("DualGuard", "Ready")

    # ---- Individual controls ----------------------------------------------
    def open_door(self) -> None:
        if not self._hw or self._servo is None:
            return
        self._servo.ChangeDutyCycle(self._angle_to_duty(config.SERVO_ANGLE_OPEN))
        time.sleep(config.DOOR_OPEN_DURATION_SEC)
        self._servo.ChangeDutyCycle(self._angle_to_duty(config.SERVO_ANGLE_CLOSED))
        time.sleep(0.5)
        self._servo.ChangeDutyCycle(0)

    def set_led(self, color: str, on: bool) -> None:
        if not self._hw:
            return
        pin = config.PIN_LED_GREEN if color == "green" else config.PIN_LED_RED
        GPIO.output(pin, GPIO.HIGH if on else GPIO.LOW)

    def blink_red(self, count: int, interval: float) -> None:
        if not self._hw:
            return
        half = max(interval / 2.0, 0.05)
        for _ in range(count):
            GPIO.output(config.PIN_LED_RED, GPIO.HIGH)
            time.sleep(half)
            GPIO.output(config.PIN_LED_RED, GPIO.LOW)
            time.sleep(half)

    def beep(self, count: int = 1) -> None:
        if not self._hw:
            return
        for i in range(count):
            GPIO.output(config.PIN_BUZZER, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(config.PIN_BUZZER, GPIO.LOW)
            if i < count - 1:
                time.sleep(0.1)

    def lcd_show(self, line1: str, line2: str = "") -> None:
        self._lcd_write(line1, line2)

    def _lcd_write(self, line1: str, line2: str = "") -> None:
        if self._lcd is None:
            return
        try:
            self._lcd.clear()
            self._lcd.write_string(line1[:config.LCD_COLS])
            if line2:
                self._lcd.crlf()
                self._lcd.write_string(line2[:config.LCD_COLS])
        except Exception as e:
            print(f"[gpio] LCD write failed: {e}")

    def cleanup(self) -> None:
        if not self._hw:
            return
        try:
            if self._lcd is not None:
                self._lcd.clear()
                self._lcd.close()
        except Exception:
            pass
        try:
            if self._servo is not None:
                self._servo.stop()
        except Exception:
            pass
        try:
            GPIO.output(config.PIN_LED_GREEN, GPIO.LOW)
            GPIO.output(config.PIN_LED_RED, GPIO.LOW)
            GPIO.output(config.PIN_BUZZER, GPIO.LOW)
            GPIO.cleanup()
        except Exception:
            pass
        print("[gpio] cleanup done")
