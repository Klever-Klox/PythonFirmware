# The clock itself: boot sequence, button handling, alarms and the main loop.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.
#
# Ported from the Arduino firmware ClockV2.3 ("Klever 2.1.11.0"). Behaviour is
# kept the same unless a comment says otherwise.

import time

import microcontroller
import rtc

from . import config, hardware, tz
from .settings import Settings, new_alarm
from .util import clamp, log, ms, wrap
from .version import NAME

MODES = ("time", "alarm", "led", "song", "settings")
SCREEN_COUNT = {"time": 7, "led": 3, "song": 1, "settings": 7}   # alarm: len(alarms) + 1
PREVIEW_DELAY_MS = 1250


class App:
    def __init__(self):
        self.s = Settings()
        self.sd_ok = False
        self.player = None
        self.leds = None
        self.inputs = None
        self.net = None
        self.web = None

        self.mode = "time"
        self.screen_mode = 0
        self.display_mode = 0
        self.day_mode = 0
        self.screen_on = True
        self.last_touch = ms()
        self.changing_until = 0
        self.preview_at = None
        self.adj_face_press = False
        self.adj_consumed = False
        self.reboot_at = None
        self.last_alarm_key = None
        self.last_wifi_check = ms()

        self._boot()

    # ------------------------------------------------------------------ boot
    def _boot(self):
        log("[BOOT]", NAME)
        spi = hardware.init_spi()
        self.ui = None
        try:
            from .ui import RED, UI, WHITE
            self.ui = UI(hardware.init_display(spi))
            splash = [("Loading...", WHITE)]
            self.ui.splash(splash)
        except Exception as e:
            log("[TFT] ERROR:", e)
            RED = WHITE = None
            splash = []

        self.sd_ok = hardware.init_sd(spi) is not None
        if self.sd_ok:
            self.s.load()
        else:
            splash.append(("No SD Card!", RED))
        self.zone = tz.Zone(self.s["zone"])

        try:
            from .audio import Player, scan_songs
            songs = scan_songs(config.SD_MOUNT) if self.sd_ok else []
            log("[SD] found %d songs" % len(songs))
            self.player = Player(songs)
            if not self.player.select_name(self.s["song"]) and songs:
                self.s["song"] = self.player.name
            self.player.set_volume(self.s["volume"])
            self.player.auto_next = self.s["autoNextSong"]
        except Exception as e:
            log("[AUDIO] ERROR:", e)

        try:
            from .leds import Leds
            self.leds = Leds()
        except Exception as e:
            log("[LED] ERROR:", e)

        try:
            from .inputs import Inputs
            self.inputs = Inputs()
            if not self.inputs.all_ok:
                splash.append(("Buttons missing!", RED))
        except Exception as e:
            log("[INPUT] ERROR:", e)
            splash.append(("Encoder/touch error", RED))

        if self.ui:
            splash.append(("Connecting WiFi...", WHITE))
            self.ui.splash(splash)

        try:
            from .net import Net
            self.net = Net()
            if self.net.connect(self.s["ssid"], self.s["password"]):
                if not self.net.sync_time(self.s["ntp"]):
                    self._restore_saved_time()
            else:
                self._restore_saved_time()
                self.net.start_ap()
            if self.net.pool:
                from .web import Web
                self.web = Web(self, self.net.pool, self.net.ap_mode)
                self.web.start(self.net.ip)
        except Exception as e:
            log("[WIFI] ERROR:", e)
            self._restore_saved_time()

        self.last_touch = ms()
        log("[BOOT] done")

    def _restore_saved_time(self):
        # No NTP: start from the time last written to settings.json, like v2.x.
        if time.localtime().tm_year >= 2025:
            return                                   # RTC survived a soft reset
        s = self.s
        try:
            local = tz.epoch(s["year"], s["month"], s["day"], s["hour"], s["min"], s["sec"])
            rtc.RTC().datetime = time.localtime(self.zone.to_utc(local))
            log("[TIME] restored from settings.json")
        except Exception as e:
            log("[TIME] could not restore:", e)

    # ----------------------------------------------------------------- time
    def local(self):
        return self.zone.local(time.time())

    def _set_local(self, y, mo, d, h, mi, sec):
        mo = wrap(mo - 1, 12) + 1
        d = clamp(d, 1, tz.days_in_month(y, mo))
        utc = self.zone.to_utc(tz.epoch(y, mo, d, h, mi, sec))
        rtc.RTC().datetime = time.localtime(utc)

    # -------------------------------------------------------------- helpers
    @property
    def playing(self):
        return bool(self.player and self.player.playing)

    def _alarm(self):
        if self.mode == "alarm" and 0 <= self.screen_mode < len(self.s.alarms):
            return self.s.alarms[self.screen_mode]
        return None

    def touch(self):
        """Any user action: wake the screen, persist and tell the web page."""
        self.last_touch = ms()
        self.screen_on = True
        self.s.mark_dirty(self.last_touch)
        self.notify()

    def notify(self):
        if self.web:
            self.web.push("settings", self.public_settings())

    def play(self, song=None, volume=None):
        if not self.player:
            return
        if song is not None:
            self.player.select_name(song)
        if volume is not None:
            self.player.set_volume(volume)
        if self.player.play():
            self.s["song"] = self.player.name
        self.s["alarmRinging"] = self.playing

    def stop(self):
        if self.player:
            self.player.stop()
        self.s["alarmRinging"] = False
        self.preview_at = None

    def _preview(self):
        # Turning to a different song plays it a moment later, like v2.x.
        self.stop()
        self.preview_at = ms() + PREVIEW_DELAY_MS

    def skip(self, direction):
        if self.player and self.player.count:
            self.s["song"] = self.player.step(direction)

    def request_reboot(self):
        self.s.save()
        self.reboot_at = ms() + 1500

    # ----------------------------------------------------------- web hooks
    def public_settings(self):
        self.s["alarmRinging"] = self.playing
        return self.s.public(self.sd_ok, bool(self.inputs and self.inputs.all_ok))

    def apply_web_settings(self, doc):
        old_song, was_playing = self.s["song"], self.playing
        self.s.apply_web(doc)
        if self.player:
            self.player.auto_next = self.s["autoNextSong"]
            self.player.set_volume(self.s["volume"])
            if self.s["song"] != old_song:
                self.player.select_name(self.s["song"])
                if was_playing:
                    self.play()
            if "alarmRinging" in doc and bool(doc["alarmRinging"]) != self.playing:
                if doc["alarmRinging"]:
                    self.play(self.s["song"])
                else:
                    self.stop()
        self.zone = tz.Zone(self.s["zone"])
        self.s.mark_dirty(ms())
        self.last_touch = ms()
        self.screen_on = True
        self.notify()

    def ota_status(self):
        return {"current": NAME, "latest": "", "state": "idle", "progress": 0,
                "message": "Python firmware: update by copying new files over USB",
                "notes": "", "supported": False, "busy": False,
                "autoUpdate": self.s["autoUpdate"], "url": self.s["otaUrl"]}

    def save_wifi(self, ssid, password):
        self.s["ssid"], self.s["password"] = ssid, password
        self.request_reboot()

    # ------------------------------------------------------------ buttons
    def on_mode(self):
        self.mode = MODES[(MODES.index(self.mode) + 1) % len(MODES)]
        self.screen_mode = self.display_mode = 0
        self.touch()

    def on_adjust_press(self):
        self.adj_face_press = self.mode == "time" and self.screen_mode == 0
        self.adj_consumed = False
        if self.adj_face_press:
            if not self.screen_on:                  # first tap only wakes it
                self.adj_consumed = True
                self.touch()
            return                                   # decided on release / hold
        count = len(self.s.alarms) + 1 if self.mode == "alarm" else SCREEN_COUNT[self.mode]
        self.screen_mode = wrap(self.screen_mode + 1, count)
        self.display_mode = 0
        self.touch()

    def on_adjust_hold(self):
        if self.adj_face_press and not self.adj_consumed:
            self.adj_consumed = True
            self.screen_mode = 1                     # start editing the hour
            self.display_mode = 0
            self.touch()

    def on_adjust_release(self):
        if self.adj_face_press and not self.adj_consumed:
            self.screen_on = False                   # short tap on the clock face: screen off
            self.s.mark_dirty(ms())
            self.notify()

    def on_ok(self):
        self.display_mode += 1
        m = self.mode
        if m == "time":
            self.skip(-1)
        elif m == "alarm":
            if self._alarm() is not None:
                if self.display_mode > 6:
                    self.display_mode = 0
            else:                                    # "[OK] -> add new alarm"
                self.s.alarms.append(new_alarm(self.s.data))
                self.display_mode = 0
        elif m == "led":
            if self.display_mode > 3:
                self.display_mode = 0
        elif m == "settings" and self.screen_mode == 5:
            self.request_reboot()
        else:
            self.display_mode = 0
        self.touch()

    def on_on(self):
        m, a = self.mode, self._alarm()
        if m == "song":
            if self.playing:
                self.stop()
            else:
                self.play(self.s["song"])
        elif m == "alarm":
            if a is not None and self.display_mode == 0:
                a["active"] = not a["active"]
            elif a is None and self.display_mode == 0:
                self.s["alarmsActive"] = not self.s["alarmsActive"]
            elif a is not None and self.display_mode == 3:
                a["days"][self.day_mode] = not a["days"][self.day_mode]
            elif a is not None and self.display_mode == 6:
                self.s.alarms.pop(self.screen_mode)
                self.display_mode = 0
        elif m == "led":
            self.s["LEDOn"] = not self.s["LEDOn"]
        elif m == "time":
            self.skip(1)
        elif m == "settings" and self.screen_mode == 6:
            self.s["autoUpdate"] = not self.s["autoUpdate"]
        self.touch()

    def on_turn(self, n):
        s, m, sm, dm = self.s, self.mode, self.screen_mode, self.display_mode
        self.changing_until = ms() + 600
        if m == "time":
            if sm == 0:
                s["volume"] = wrap(s["volume"] + n, 101)
                if self.player:
                    self.player.set_volume(s["volume"])
            else:
                t = self.local()
                y, mo, d, h, mi, sec = t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec
                if sm == 1:
                    h = wrap(h + n, 24)
                elif sm == 2:
                    mi = wrap(mi + n, 60)
                elif sm == 3:
                    sec = wrap(sec + n, 60)
                elif sm == 4:
                    mo += n
                elif sm == 5:
                    d = wrap(d - 1 + n, tz.days_in_month(y, mo)) + 1
                elif sm == 6:
                    y = clamp(y + n, 2000, 2099)
                self._set_local(y, mo, d, h, mi, sec)
        elif m == "alarm":
            a = self._alarm()
            if a is not None:
                if dm == 1:
                    a["hour"] = wrap(a["hour"] + n, 24)
                elif dm == 2:
                    a["minute"] = wrap(a["minute"] + n, 60)
                elif dm == 3:
                    self.day_mode = wrap(self.day_mode + n, 7)
                elif dm == 4:
                    a["volume"] = wrap(a["volume"] + n, 101)
                elif dm == 5 and self.player and self.player.count:
                    self.player.select_name(a["song"])
                    self.player.index = wrap(self.player.index + n, self.player.count)
                    a["song"] = s["song"] = self.player.name
                    self._preview()
        elif m == "led":
            if sm == 1:
                s["hue"] = wrap(s["hue"] + n, 256)
            elif sm == 2:
                s["brightness"] = wrap(s["brightness"] + n, 256)
        elif m == "song":
            if self.player and self.player.count:
                self.player.index = wrap(self.player.index + n, self.player.count)
                s["song"] = self.player.name
                self._preview()
        elif m == "settings":
            if sm == 1:
                s["volume"] = wrap(s["volume"] + n, 101)
                if self.player:
                    self.player.set_volume(s["volume"])
            elif sm == 2:
                s["contrast"] = wrap(s["contrast"] + n, 256)
        self.touch()

    def on_knob(self, kind):
        if kind == "hold":
            log("[KNOB] held - saving and restarting")
            self.request_reboot()
            return
        if self.playing:
            self.stop()
        else:
            self.play(self.s["song"], self.s["volume"])
        self.touch()

    # -------------------------------------------------------------- alarms
    def check_alarms(self, t):
        if self.playing or not self.s["alarmsActive"]:
            return
        key = (t.tm_yday, t.tm_hour, t.tm_min)
        if key == self.last_alarm_key:
            return                                   # already fired this minute
        today = (t.tm_wday + 1) % 7                  # Sunday = 0, like v2.x
        for a in self.s.alarms:
            if a["active"] and a["days"][today] and a["hour"] == t.tm_hour and a["minute"] == t.tm_min:
                self.last_alarm_key = key
                log("[ALARM] %02d:%02d ringing" % (a["hour"], a["minute"]))
                if self.s["fadeOn"] and a["fadeOn"]:
                    self.s["LEDOn"] = True
                    self.s["colour"] = a["colour"]
                self.s["volume"] = a["volume"]
                self.play(a["song"], a["volume"])
                self.screen_on = True
                self.last_touch = ms()
                self.notify()
                return

    # ---------------------------------------------------------------- loop
    def _ui_state(self, now, t):
        p = self.player
        return {
            "mode": self.mode, "screen_mode": self.screen_mode, "display_mode": self.display_mode,
            "day_mode": self.day_mode, "screen_on": self.screen_on,
            "night_screen": self.s["nightScreen"], "scheme": wrap(self.s["colourScheme"], 3),
            "t": t, "twelve": self.s["twelveHour"],
            "blink": (now // 500) % 2 == 0 and now >= self.changing_until,
            "changing": now < self.changing_until,
            "playing": self.playing, "song": self.s["song"], "volume": self.s["volume"],
            "song_index": p.index if p else 0, "song_count": p.count if p else 0,
            "alarm": self._alarm(), "alarms_active": self.s["alarmsActive"],
            "hue": self.s["hue"], "brightness": self.s["brightness"],
            "led_on": self.s["LEDOn"], "contrast": self.s["contrast"],
            "ip": self.net.ip if self.net else "", "ap_mode": bool(self.net and self.net.ap_mode),
            "ap_ssid": config.AP_SSID, "wifi": bool(self.net and self.net.connected),
            "sd_ok": self.sd_ok,
        }

    def run(self):
        last_ui = last_led = 0
        while True:
            now = ms()

            if self.inputs:
                for ev in self.inputs.poll():
                    kind, what = ev[0], ev[1]
                    if kind == "press":
                        if what == "MODE":
                            self.on_mode()
                        elif what == "ADJUST":
                            self.on_adjust_press()
                        elif what == "OK":
                            self.on_ok()
                        elif what == "ON":
                            self.on_on()
                    elif kind == "hold":
                        self.on_adjust_hold()
                    elif kind == "release" and what == "ADJUST":
                        self.on_adjust_release()
                    elif kind == "turn":
                        self.on_turn(what)
                    elif kind == "knob":
                        self.on_knob(what)

            if self.player:
                if self.player.update():
                    self.s["song"] = self.player.name
                    self.s["alarmRinging"] = self.playing
                    self.notify()
                if self.preview_at is not None and now >= self.preview_at:
                    self.preview_at = None
                    self.play(self.s["song"])

            if now - last_ui >= config.UI_REFRESH_MS:
                last_ui = now
                t = self.local()
                self.check_alarms(t)
                if (self.s["screenSwitchOff"] and self.screen_on
                        and now - self.last_touch > config.SCREEN_TIMEOUT_MS):
                    self.mode, self.screen_mode, self.display_mode = "time", 0, 0
                    self.screen_on = False
                if self.ui:
                    self.ui.render(self._ui_state(now, t))
                if self.leds and now - last_led >= 100:
                    last_led = now
                    self.leds.update(self.s, self.s.alarms, t, self.mode == "led")

            if self.web:
                self.web.poll()

            if self.net and not self.net.ap_mode and now - self.last_wifi_check > config.WIFI_RECHECK_MS:
                self.last_wifi_check = now
                if self.net.check() or self.net.connect(self.s["ssid"], self.s["password"]):
                    self.net.sync_time(self.s["ntp"])
                self.notify()

            if self.sd_ok and self.s.dirty_since is not None:
                if now - self.s.dirty_since >= config.SAVE_DELAY_MS:
                    self._store_time()
                    self.s.save()

            if self.reboot_at is not None and now >= self.reboot_at:
                log("[BOOT] restarting")
                microcontroller.reset()

    def _store_time(self):
        t = self.local()
        self.s.data.update(sec=t.tm_sec, min=t.tm_min, hour=t.tm_hour,
                           day=t.tm_mday, month=t.tm_mon, year=t.tm_year)
