# DualGuard Wiring (BCM)

`gpio_controller.py` uses `GPIO.setmode(GPIO.BCM)`. All pin numbers in
`config.py` are **BCM**, not physical/BOARD numbers.

## Pin map

| Component       | config.py constant   | BCM   | Physical pin | Notes                          |
|-----------------|----------------------|-------|--------------|--------------------------------|
| Servo signal    | `PIN_SERVO`          | 18    | 12           | SG90, 50 Hz PWM                |
| Green LED       | `PIN_LED_GREEN`      | 23    | 16           | 220 Ω series resistor          |
| Red LED         | `PIN_LED_RED`        | 24    | 18           | 220 Ω series resistor          |
| Active buzzer   | `PIN_BUZZER`         | 25    | 22           | Active type (HIGH = on)        |
| LCD 1602 SDA    | (I2C fixed)          | 2     | 3            | I2C addr `0x27` (PCF8574)      |
| LCD 1602 SCL    | (I2C fixed)          | 3     | 5            |                                |
| 5V power        | —                    | —     | 2 or 4       | LCD VCC, optional servo VCC    |
| 3.3V power      | —                    | —     | 1 or 17      | unused                         |
| GND (common)    | —                    | —     | 6/9/14/20/25/30/34/39 | tie all GNDs together |

## Servo power warning

SG90 stall current can pull >500 mA briefly. Powering it from the Pi's 5V
rail often causes brownout reboots. **Use an external 5V supply** (e.g. a
separate USB-5V module or 4×AA pack) for the servo VCC, and just share
GND with the Pi.

```
                +-------------+
External 5V ----+ VCC         |
                |    SG90     |---- signal -> Pi BCM 18 (phys 12)
Common GND -----+ GND         |
                +-------------+
```

## LED + resistor

```
Pi BCM 23 (phys 16) ----[220Ω]----|>|---- GND     # green
Pi BCM 24 (phys 18) ----[220Ω]----|>|---- GND     # red
```

Long leg (anode) goes toward the Pi pin.

## Active buzzer

```
Pi BCM 25 (phys 22) ----+ (+)
                        |  Buzzer
GND ---------------------+ (-)
```

If it sounds even when GPIO is LOW, polarity is reversed.

## LCD 1602 (I2C, PCF8574 backpack)

```
LCD VCC -> Pi 5V    (phys 2 or 4)
LCD GND -> Pi GND
LCD SDA -> Pi SDA   (BCM 2,  phys 3)
LCD SCL -> Pi SCL   (BCM 3,  phys 5)
```

Verify the I2C address after wiring:

```bash
sudo i2cdetect -y 1
```

If the address shown is not `0x27` (commonly `0x3F` on some backpacks),
update `LCD_I2C_ADDRESS` in `config.py`.

## Pi 40-pin header reference (quick view)

```
  3V3  (1) (2)  5V
  SDA  (3) (4)  5V        <- LCD VCC
  SCL  (5) (6)  GND       <- common GND
       (7) (8)
  GND  (9) (10)
       (11)(12) BCM18     <- servo signal
       (13)(14) GND
       (15)(16) BCM23     <- green LED
       (17)(18) BCM24     <- red LED
       (19)(20) GND
       (21)(22) BCM25     <- buzzer
       ...
```

(Only the rows used by DualGuard are highlighted — full pinout: `pinout`
command on Pi OS.)

## Sanity check before running `main.py`

```bash
# I2C enabled?
sudo raspi-config       # Interface Options -> I2C -> Enable
sudo i2cdetect -y 1     # LCD address should appear

# Python deps for hardware
pip install RPi.GPIO RPLCD smbus2

# Quick GPIO smoke test (without full pipeline)
python -c "from modules.gpio_controller import GPIOController; \
g = GPIOController(); g.beep(2); g.set_led('green', True); \
import time; time.sleep(1); g.set_led('green', False); \
g.open_door(); g.cleanup()"
```

If all four (servo motion, green LED on/off, two beeps, LCD "DualGuard /
Ready") fire, hardware is good and you can run `python main.py`.
