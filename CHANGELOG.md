# Changelog

Versions are `MAJOR.MINOR.PATCH.BUILD`, like the Arduino firmware.

## 1.0.0.0 - 2026-11-25

First release of the CircuitPython firmware. It is a port of the Arduino
firmware ClockV2.3 ("Klever 2.1.11.0"), built so that no compiling is needed:
updating the clock means copying files onto the `CIRCUITPY` drive.

### Same as the Arduino firmware
- Clock face with 12/24-hour time, date, and the current song and volume.
- Time editing (hold ADJUST for 2 s), alarm editing, light, song and settings screens.
- Alarms with days, volume, song and a 30-minute sunrise light fade.
- MP3 playback from the SD card through the MAX98357A, with auto-next.
- WS2813 light with presets, custom hue and brightness, and rainbow.
- Touch pads, rotary encoder with acceleration, and knob click and hold (5 s to restart).
- Screen timeout and the dim red night clock.
- WiFi with NTP, mDNS at `http://kleverklox.local`, and the `Klever_Klox` setup access point.
- Local web page and API (`/api/settings`, `/songs`, `/events`), so the existing
  `index.html`, `app.js` and `style.css` on the SD card work unchanged.
- `settings.json` uses the same format, so existing SD cards keep their settings and alarms.

### Changed
- **Single SPI bus**: the TFT and the microSD card share SCK GPIO36, MOSI GPIO35 and MISO GPIO37.
- Nothing blocks any more. Button presses, web requests and audio all run from one
  loop, so the screen and music no longer freeze while a pad is held.
- Time zones: the RTC holds UTC and the POSIX `zone` string is applied in firmware.
- Settings are saved 10 s after the last change instead of every 11th touch.
- Month and day editing now stay inside 1-12 and 1-28/29/30/31.
- A faulty touch pad is disabled after 10 s held, instead of 3 s.

### Not yet ported
- Over-the-air firmware updates. `/api/ota` reports `supported: false`; updates are by USB.
- The FreeSans fonts. The built-in terminal font is used, scaled up.
- The captive-portal DNS redirect in setup mode. Browse to `http://192.168.4.1`.
