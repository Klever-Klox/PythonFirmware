# Klever Klox — CircuitPython firmware

Firmware for the Klever Klox alarm clock, written in CircuitPython for the
**LOLIN S2 Mini (ESP32-S2)**. Updating it doesn't require compiling: plug the
clock in, copy the files across, and it restarts with the new code.

> **Proprietary software.** This repository is public for reference only. You may
> not use, copy, modify or distribute any of it. See [LICENSE](LICENSE).

Current version: **1.0.0.0**. See [CHANGELOG.md](CHANGELOG.md).

---

## Hardware

| Part | Model |
|---|---|
| Board | LOLIN S2 Mini (ESP32-S2, 4 MB flash, 2 MB PSRAM) |
| Display | 1.8" ST7735 160×128 TFT (black tab; set `SCREEN_TYPE = "green"` for green tab) |
| Storage | microSD card (SPI), FAT32 |
| Audio | MAX98357A I²S amplifier and speaker |
| Light | 14 × WS2813, 330 Ω on data, 1000 µF across 5 V–GND |
| Knob | Rotary encoder: bare EC11 or KY-040 |
| Buttons | 4 capacitive touch pads (copper pad or foil) |

### Wiring: single shared SPI bus

The TFT and the SD card share **one** SPI bus. Each has its own chip-select.

| Signal | GPIO | Goes to |
|---|---|---|
| SPI SCK | **36** | TFT `SCL` **and** SD `SCK` |
| SPI MOSI | **35** | TFT `SDA` **and** SD `MOSI` |
| SPI MISO | **37** | SD `MISO` (the TFT has no MISO) |
| TFT CS | 6 | TFT `CS` |
| TFT DC | 8 | TFT `DC` / `A0` |
| TFT RESET | 7 | TFT `RES` |
| TFT backlight | **11** | TFT `BL` / `BLK` / `LED`. **Required:** without it the screen may stay dark and brightness can't be changed |
| SD CS | 34 | SD `CS` |
| I²S BCLK | 40 | amp `BCLK` |
| I²S LRC | 39 | amp `LRC` |
| I²S DIN | 38 | amp `DIN` |
| LED data | 5 | strip `DIN` (through 330 Ω) |
| Encoder A | 12 | encoder `CLK` / A |
| Encoder B | 13 | encoder `DT` / B |
| Encoder switch | 14 | encoder `SW` |
| Touch MODE | 4 | pad |
| Touch ADJUST | 2 | pad |
| Touch ON | 3 | pad |
| Touch OK | 1 | pad |

Power: TFT, SD and encoder from **3V3**; amp and LED strip from **5V (VBUS)**; all GNDs common.

**Bare EC11 encoder** (no breakout board): the middle pin of the 3-pin side goes to
**GND**, the two outer pins go to GPIO12 and GPIO13, one switch pin goes to GPIO14 and
the other switch pin goes to **GND**. Nothing on the encoder connects to 3V3. If the knob
turns the wrong way, swap `ENC_A` and `ENC_B` in [`src/klever/config.py`](src/klever/config.py).

All pins are defined in [`src/klever/config.py`](src/klever/config.py).

---

## Installing

### 1. Put CircuitPython on the board (once)

1. Open the LOLIN S2 Mini page on circuitpython.org (search "lolin s2 mini") and use
   **Open Installer** (Chrome or Edge), or download the `.bin` / `.uf2`.
2. To put the board into download mode: **hold `0`, tap `RST`, release `0`**.
3. Install CircuitPython **9.2 or newer**. When it finishes, **press `RST`**.
4. A drive called **`CIRCUITPY`** appears.

### 2. Copy the firmware

On Windows:

```powershell
pip install circup
powershell -ExecutionPolicy Bypass -File tools\deploy.ps1
```

That copies `src/code.py` and `src/klever/` onto `CIRCUITPY` and installs the
libraries in [`requirements.txt`](requirements.txt) into `CIRCUITPY/lib`.

To do it by hand instead:
- copy `src/code.py` and the `src/klever` folder to the root of `CIRCUITPY`;
- copy these folders/files from the Adafruit CircuitPython **library bundle**
  (matching your CircuitPython version) into `CIRCUITPY/lib`: `adafruit_st7735r`,
  `adafruit_display_text/`, `neopixel`, `adafruit_ntp`, `adafruit_httpserver/`.

### 3. Prepare the SD card

Format it FAT32 and copy everything in [`sd/`](sd) to the root of the card:

| File | Purpose |
|---|---|
| `settings.json` | settings and alarms (same format as the Arduino firmware, so an old card works as-is) |
| `index.html`, `app.js`, `style.css` | the clock's web page |
| `*.mp3` | your alarm sounds, anywhere on the card |

---

## First start

1. With no WiFi saved, the clock starts an open access point named **`Klever_Klox`**.
2. Join it and browse to **`http://192.168.4.1`**, enter your WiFi details, and save.
3. The clock restarts, joins your network and sets the time from NTP. Its page is then at
   **`http://kleverklox.local`**, or at the IP shown under *Settings → IP Address*.

## Using the clock

| Control | Clock face | Elsewhere |
|---|---|---|
| **MODE** | next screen: time → alarm → light → song → settings | |
| **ADJUST** | tap: screen off · hold 2 s: edit time (each tap moves to the next field) | next page / field |
| **OK** | previous song | next alarm field · add alarm · restart (settings) |
| **ON** | next song | play/stop · alarm on/off · toggle day · delete alarm · light on/off |
| **Knob turn** | volume | change the selected value |
| **Knob click** | play / stop | |
| **Knob hold 5 s** | save settings and restart | |

---

## Debugging

- **Serial console**: connect at any baud rate with PuTTY, the Arduino Serial Monitor,
  Thonny or Mu to see the boot log (`[SD]`, `[WIFI]`, `[TOUCH]` …) and any error.
  **Ctrl+C** stops the firmware and opens the REPL; **Ctrl+D** restarts it.
- **One part at a time**: [`tests/hardware/`](tests/hardware) has a small test for each
  part (TFT, SD, audio, LEDs, inputs, WiFi). For example:
  ```powershell
  powershell -ExecutionPolicy Bypass -File tools\deploy.ps1 -Test test_tft
  ```
  To go back to the clock firmware, run `deploy.ps1` with no `-Test`.
- **Touch pads not responding / triggering on their own**: set `DEBUG_TOUCH = True` in
  `config.py`, watch the raw readings, and set `TOUCH_THRESHOLD` between the
  untouched and touched values.
- **A part failing doesn't stop the clock.** A missing SD card, display, LED strip
  or touch pad is logged and skipped, and the rest keeps running.
- **High-pitched whine from the speaker** while nothing is playing usually means the
  firmware isn't running, which leaves the I²S pins floating. Check the serial console.

Desktop unit tests (time-zone maths): `python -m unittest discover -s tests`

## Repository layout

```
src/code.py            entry point (goes on CIRCUITPY)
src/klever/            the firmware package (goes on CIRCUITPY)
  config.py            pins and constants
  app.py               main loop, buttons, alarms
  ui.py, icons.py      display
  audio.py             MP3 player
  leds.py              LED strip
  inputs.py            touch pads + encoder
  net.py, web.py       WiFi, NTP, mDNS, web page/API
  settings.py, tz.py   settings.json, time zones
sd/                    files for the SD card
tests/hardware/        one-part-at-a-time hardware tests
tools/deploy.ps1       copy to CIRCUITPY + install libraries
```

## Releases

Each release is tagged `vMAJOR.MINOR.PATCH.BUILD` and has a `KleverKlox-<version>.zip`
holding `code.py`, `klever/` and `sd/`.

## Security

See [SECURITY.md](SECURITY.md). Report vulnerabilities privately, not in public issues.
