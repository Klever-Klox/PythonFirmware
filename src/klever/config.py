# Klever Klox - hardware and behaviour constants.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.
#
# Everything wiring-related lives here so a board revision only touches this file.
# Pin names are the LOLIN S2 Mini's (board.IO<n> == GPIO<n>).

import board

# ---- Single shared SPI bus (TFT + microSD) ----
SPI_SCK = board.IO36
SPI_MOSI = board.IO35
SPI_MISO = board.IO37

TFT_CS = board.IO6
TFT_DC = board.IO8
TFT_RST = board.IO7
TFT_BL = board.IO11          # backlight, PWM-dimmed. Must be wired for brightness control.
TFT_BAUDRATE = 24_000_000

# "black" = ST7735 black-tab (the original screen), "green" = green-tab (NEWSCREEN in v2.x)
SCREEN_TYPE = "black"

SD_CS = board.IO34
SD_BAUDRATE = 10_000_000     # same as the Arduino build; raise only once stable
SD_MOUNT = "/sd"

# ---- I2S amplifier (MAX98357A) ----
I2S_BCLK = board.IO40
I2S_LRC = board.IO39
I2S_DIN = board.IO38

# ---- WS2813 LED strip ----
LED_PIN = board.IO5
NUM_LEDS = 14
LED_MAX_BRIGHTNESS = 150     # 0-255, same cap as v2.x
LED_FADE_MINUTES = 30        # sunrise fade length before an alarm

# ---- Rotary encoder ----
# Bare EC11 or KY-040 both work: the firmware relies on the internal pull-ups.
# Swap these two (or the wires) if turning the knob goes the wrong way.
ENC_A = board.IO12
ENC_B = board.IO13
ENC_SW = board.IO14
ENC_DIVISOR = 4              # detents: 4 quadrature edges per click

# ---- Capacitive touch pads ----
TOUCH_MODE = board.IO4
TOUCH_ADJ = board.IO2
TOUCH_ON = board.IO3
TOUCH_OK = board.IO1
# A pad counts as pressed when its raw reading rises above this. 10000 is the
# value the Arduino firmware used on the same hardware. Set DEBUG_TOUCH = True
# to print raw readings and tune it for your pads.
TOUCH_THRESHOLD = 10000
TOUCH_STUCK_MS = 10_000      # a pad "held" this long is treated as faulty and ignored

# ---- Behaviour ----
SCREEN_TIMEOUT_MS = 60_000
ADJ_HOLD_MS = 2_000          # hold ADJUST on the clock face to edit the time
KNOB_RESTART_MS = 5_000      # hold the knob to save and restart
WIFI_RECHECK_MS = 60 * 60_000
SAVE_DELAY_MS = 10_000       # settings are written this long after the last change
UI_REFRESH_MS = 100

MDNS_HOSTNAME = "kleverklox"
AP_SSID = "Klever_Klox"
SETTINGS_FILE = SD_MOUNT + "/settings.json"

# ---- Debug ----
DEBUG = True
DEBUG_TOUCH = False
