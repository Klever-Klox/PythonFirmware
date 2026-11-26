# Settings, stored on the SD card as /settings.json in the same format the
# Arduino firmware (v2.x) used, so an existing card keeps working.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

import json

from . import config
from .util import clamp, log

DEFAULTS = {
    "colour": "Custom",
    "ssid": "",
    "password": "",
    "ntp": "pool.ntp.org",
    "zone": "IST-1GMT0,M10.5.0,M3.5.0/1",   # Ireland
    "sec": 0, "min": 0, "hour": 0, "day": 1, "month": 1, "year": 2026,
    "hue": 255,
    "brightness": 255,
    "contrast": 255,
    "colourScheme": 0,
    "volume": 100,            # held as 0-100 in memory, 0.0-1.0 on disk / on the API
    "twelveHour": True,
    "alarmsActive": True,
    "alarmRinging": False,
    "LEDOn": False,
    "fadeOn": False,
    "screenSwitchOff": True,
    "autoNextSong": True,
    "nightScreen": True,
    "autoUpdate": True,
    "otaUrl": "",
    "song": "",
}

# Fields the web page may change (credentials only come through AP setup).
WEB_FIELDS = ("colour", "hue", "brightness", "contrast", "twelveHour", "alarmsActive",
              "LEDOn", "screenSwitchOff", "autoNextSong", "fadeOn", "nightScreen",
              "autoUpdate", "otaUrl", "song", "colourScheme")

COLOURS = ("Custom", "Red", "Blue", "Green", "Yellow", "Magenta", "Cyan", "White", "Rainbow")


def vol_in(v, default=100):
    """Accept 0.0-1.0 (v2.x format) or 0-100 and return an int percentage."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return default
    if v <= 1.0:
        v *= 100
    return int(clamp(v, 0, 100) + 0.5)


def new_alarm(s):
    return {"hour": 6, "minute": 30, "days": [True] * 7, "volume": s["volume"],
            "fadeOn": s["fadeOn"], "colour": s["colour"], "active": True, "song": s["song"]}


def _alarm_in(a, s):
    days = [False] * 7
    raw = a.get("days", [])
    if len(raw) == 7 and all(isinstance(d, bool) for d in raw):
        days = list(raw)                      # settings.json: 7 booleans
    else:
        for d in raw:                          # web API: list of day indices ("0".."6")
            try:
                d = int(d)
            except (TypeError, ValueError):
                continue
            if 0 <= d < 7:
                days[d] = True
    return {
        "hour": int(a.get("hour", 6)) % 24,
        "minute": int(a.get("minute", 30)) % 60,
        "days": days,
        "volume": vol_in(a.get("volume", 1.0)),
        "fadeOn": bool(a.get("fadeOn", s["fadeOn"])),
        "colour": str(a.get("colour", s["colour"])),
        "active": bool(a.get("active", s["alarmsActive"])),
        "song": str(a.get("song", s["song"])),
    }


class Settings:
    def __init__(self):
        self.data = dict(DEFAULTS)
        self.alarms = []
        self.dirty_since = None

    def __getitem__(self, k):
        return self.data[k]

    def __setitem__(self, k, v):
        self.data[k] = v

    # ---- SD card ----
    def load(self):
        try:
            with open(config.SETTINGS_FILE, "r") as f:
                doc = json.load(f)
        except OSError:
            log("[SETTINGS] no settings.json - using defaults")
            return False
        except ValueError as e:
            log("[SETTINGS] settings.json is not valid JSON:", e)
            return False
        for k, v in DEFAULTS.items():
            if k in doc and k != "volume":
                self.data[k] = type(v)(doc[k]) if not isinstance(v, str) else str(doc[k])
        self.data["volume"] = vol_in(doc.get("volume", 1.0))
        self.data["alarmRinging"] = False
        self.alarms = [_alarm_in(a, self.data) for a in doc.get("alarms", [])]
        log("[SETTINGS] loaded, %d alarms" % len(self.alarms))
        return True

    def save(self):
        doc = dict(self.data)
        doc["volume"] = self.data["volume"] / 100
        doc["alarms"] = [dict(a, volume=a["volume"] / 100) for a in self.alarms]
        try:
            with open(config.SETTINGS_FILE, "w") as f:
                json.dump(doc, f)
            self.dirty_since = None
            log("[SETTINGS] saved")
            return True
        except OSError as e:
            log("[SETTINGS] save failed:", e)
            return False

    def mark_dirty(self, now):
        self.dirty_since = now

    def save_if_due(self, now):
        if self.dirty_since is not None and now - self.dirty_since >= config.SAVE_DELAY_MS:
            self.save()

    # ---- web API ----
    def public(self, sd_ok, buttons_ok):
        out = {k: self.data[k] for k in WEB_FIELDS}
        out["volume"] = self.data["volume"] / 100
        out["alarmRinging"] = self.data["alarmRinging"]
        out["sdCardOk"] = sd_ok
        out["buttonsOk"] = buttons_ok
        out["alarms"] = [
            dict(a, volume=a["volume"] / 100, days=[str(i) for i in range(7) if a["days"][i]])
            for a in self.alarms
        ]
        return out

    def apply_web(self, doc):
        for k in WEB_FIELDS:
            if k in doc:
                default = DEFAULTS[k]
                try:
                    self.data[k] = str(doc[k]) if isinstance(default, str) else type(default)(doc[k])
                except (TypeError, ValueError):
                    pass
        for k in ("hue", "brightness", "contrast"):
            self.data[k] = int(clamp(self.data[k], 0, 255))
        if "volume" in doc:
            self.data["volume"] = vol_in(doc["volume"], self.data["volume"])
        if isinstance(doc.get("alarms"), list):
            self.alarms = [_alarm_in(a, self.data) for a in doc["alarms"]]
