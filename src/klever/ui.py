# Everything drawn on the 160x128 ST7735.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.
#
# displayio is retained-mode: each screen is a set of labels whose text we
# change, and the display is refreshed only when something actually changed.
# That keeps the shared SPI bus free for the SD card (and the music) the rest
# of the time.

import displayio
import terminalio
import vectorio
from adafruit_display_text.label import Label

from . import icons
from .version import BOARD, NAME

WHITE, BLACK, RED, GREEN, BLUE = 0xFFFFFF, 0x000000, 0xFF0000, 0x00FF00, 0x0000FF
GREY = 0x7A7A7A

# (background, time, text) per colour scheme - same RGB values as v2.x
SCHEMES = (
    (0x387315, BLUE, WHITE),
    (0x733815, RED, GREY),
    (0x381573, GREEN, BLACK),
)
SELECTED, DESELECTED = GREEN, RED
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
WDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")     # struct_time order
DAY_LETTERS = "SMTWTFS"                                       # alarm order, Sunday first
FONT = terminalio.FONT


class UI:
    def __init__(self, display):
        self.display = display
        self.root = displayio.Group()
        self.bg_pal = displayio.Palette(1)
        self.bg_pal[0] = SCHEMES[0][0]
        self.root.append(vectorio.Rectangle(pixel_shader=self.bg_pal, width=160, height=128,
                                            x=0, y=0))
        self.content = displayio.Group()
        self.root.append(self.content)

        self.status = displayio.Group()
        self.ic_alarm = icons.Icon({"on": icons.ALARM_ON, "off": icons.ALARM_OFF}, 10, 104)
        self.ic_light = icons.Icon({"on": icons.LIGHT_ON}, 50, 104)
        self.ic_wifi = icons.Icon({"on": icons.WIFI_ON, "off": icons.WIFI_OFF}, 90, 104)
        for ic in (self.ic_alarm, self.ic_light, self.ic_wifi):
            self.status.append(ic.grid)
        self.sd_label = Label(FONT, text="SD!", color=RED, x=130, y=112)
        self.status.append(self.sd_label)
        self.root.append(self.status)

        self.L = {}
        self.screen_key = None
        self.dirty = True
        self.brightness = None
        display.root_group = self.root

    # ---- helpers ----
    def _clear(self):
        while len(self.content):
            self.content.pop()
        self.L = {}

    def _add(self, key, x, y, scale=1, color=WHITE):
        lab = Label(FONT, text=" ", color=color, scale=scale, x=x, y=y)
        self.content.append(lab)
        self.L[key] = lab

    def _set(self, key, text, hidden=False, color=None):
        lab = self.L[key]
        text = str(text) if text != "" else " "
        if lab.text != text:
            lab.text = text
            self.dirty = True
        if lab.hidden != hidden:
            lab.hidden = hidden
            self.dirty = True
        if color is not None and lab.color != color:
            lab.color = color
            self.dirty = True

    def set_backlight(self, level):          # 0-255
        if level != self.brightness:
            self.brightness = level
            self.display.brightness = level / 255

    def splash(self, lines):
        self._clear()
        self.screen_key = None
        for i, (text, color) in enumerate(lines):
            self._add(i, 10, 20 + i * 16, 1, color)
            self._set(i, text)
        self.status.hidden = True
        self.display.refresh(target_frames_per_second=None)

    # ---- screen builders ----
    def _build(self, key, st):
        self._clear()
        self.screen_key = key
        mode = key[0]
        _, tcol, xcol = SCHEMES[st["scheme"]]
        if mode == "night":
            self._add("hour", 8, 64, 4, RED)
            self._add("colon", 52, 62, 4, RED)
            self._add("min", 72, 64, 4, RED)
            self._add("ampm", 126, 52, 1, RED)
        elif mode == "time":
            self._add("hour", 6, 26, 4, tcol)
            self._add("colon", 50, 24, 4, tcol)
            self._add("min", 70, 26, 4, tcol)
            self._add("sec", 124, 34, 2, tcol)
            self._add("ampm", 126, 12, 1, tcol)
            self._add("wday", 6, 62, 2, xcol)
            self._add("month", 60, 62, 2, xcol)
            self._add("mday", 108, 62, 2, xcol)
            self._add("song", 6, 82, 1, xcol)
            self._add("vol", 6, 94, 1, xcol)
        elif mode == "alarm":
            self._add("title", 10, 12, 2, xcol)
            self._add("hour", 20, 42, 3, xcol)
            self._add("colon", 56, 40, 3, xcol)
            self._add("min", 74, 42, 3, xcol)
            self._add("line", 10, 74, 2, xcol)
            self._add("small", 10, 74, 1, xcol)
            self._add("small2", 10, 90, 1, xcol)
            for i in range(7):
                self._add("d%d" % i, 20 + i * 14, 74, 2, DESELECTED)
            self._add("cursor", 20, 86, 2, SELECTED)
        else:                                  # led / song / settings: title + 3 lines
            self._add("title", 10, 14, 2, xcol)
            self._add("big", 10, 46, 2, xcol)
            self._add("l1", 10, 40, 1, xcol)
            self._add("l2", 10, 56, 1, xcol)
            self._add("l3", 10, 72, 1, xcol)
        self.dirty = True

    # ---- per-frame rendering ----
    def render(self, st):
        """st is a plain dict of everything the screen needs (built by the app)."""
        if not st["screen_on"]:
            mode = "night" if st["night_screen"] else "off"
        else:
            mode = st["mode"]
        key = (mode, st["scheme"])
        if key != self.screen_key:
            self._build(key, st)

        bg = BLACK if mode in ("night", "off") else SCHEMES[st["scheme"]][0]
        if self.bg_pal[0] != bg:
            self.bg_pal[0] = bg
            self.dirty = True
        status_hidden = mode in ("night", "off")
        if self.status.hidden != status_hidden:
            self.status.hidden = status_hidden
            self.dirty = True

        if mode == "off":
            self.set_backlight(0)
        elif mode == "night":
            self.set_backlight(5)
            self._render_night(st)
        else:
            self.set_backlight(max(st["contrast"], 1))
            getattr(self, "_render_" + mode)(st)
            self._render_status(st)

        if self.dirty:
            self.dirty = False
            self.display.refresh(target_frames_per_second=None)

    def _hm(self, t, twelve):
        h = t.tm_hour
        ampm = ""
        if twelve:
            ampm = "PM" if h >= 12 else "AM"
            h = h % 12 or 12
        return "%02d" % h, "%02d" % t.tm_min, ampm

    def _render_night(self, st):
        h, m, ampm = self._hm(st["t"], st["twelve"])
        self._set("hour", h)
        self._set("colon", ":")
        self._set("min", m)
        self._set("ampm", ampm, hidden=not ampm)

    def _render_time(self, st):
        t, edit, blink = st["t"], st["screen_mode"], st["blink"]
        h, m, ampm = self._hm(t, st["twelve"])
        self._set("hour", h, hidden=edit == 1 and blink)
        self._set("colon", ":")
        self._set("min", m, hidden=edit == 2 and blink)
        self._set("sec", "%02d" % t.tm_sec, hidden=edit == 3 and blink)
        self._set("ampm", ampm, hidden=not ampm)
        if edit == 6:
            self._set("wday", t.tm_year, hidden=blink)
            self._set("month", "", hidden=True)
            self._set("mday", "", hidden=True)
        else:
            self._set("wday", WDAYS[t.tm_wday])
            self._set("month", MONTHS[t.tm_mon - 1], hidden=edit == 4 and blink)
            self._set("mday", t.tm_mday, hidden=edit == 5 and blink)
        show_song = edit == 0
        self._set("song", (">" if st["playing"] else " ") + " " + st["song"][:24],
                  hidden=not show_song)
        self._set("vol", "Vol: %d" % st["volume"], hidden=not show_song)

    def _render_alarm(self, st):
        a, dm, blink = st["alarm"], st["display_mode"], st["blink"]
        if a is None:                          # "add alarm" page
            for k in ("hour", "colon", "min", "line", "cursor") + tuple("d%d" % i for i in range(7)):
                self._set(k, "", hidden=True)
            self._set("title", "Alarms", hidden=False)
            self._set("small", "[ON] -> turn alarms " + ("off" if st["alarms_active"] else "on"))
            self._set("small2", "[OK] -> add new alarm")
            return
        self._set("title", "Alarm #%d" % st["screen_mode"])
        self._set("hour", "%02d" % a["hour"], hidden=dm == 1 and blink)
        self._set("colon", ":")
        self._set("min", "%02d" % a["minute"], hidden=dm == 2 and blink)
        days = dm == 3
        for i in range(7):
            self._set("d%d" % i, DAY_LETTERS[i], hidden=not days,
                      color=SELECTED if a["days"][i] else DESELECTED)
        self._set("cursor", "_", hidden=not days)
        if days:
            self.L["cursor"].x = 20 + st["day_mode"] * 14
            self.dirty = True
        line, small, small2 = "", "", ""
        if dm in (0, 1, 2):
            line = "active" if a["active"] else "inactive"
        elif dm == 4:
            line = "Vol: %d" % a["volume"]
        elif dm == 5:
            small = "%d %s" % (st["song_index"], a["song"][:22])
            small2 = "turn knob to pick"
        elif dm == 6:
            small = "[ON] -> Delete Alarm"
        self._set("line", line, hidden=not line)
        self._set("small", small, hidden=not small)
        self._set("small2", small2, hidden=not small2)

    def _lines(self, title, big="", l1="", l2="", l3="", big_hidden=False):
        self._set("title", title)
        self._set("big", big, hidden=not big or big_hidden)
        self._set("l1", l1, hidden=not l1)
        self._set("l2", l2, hidden=not l2)
        self._set("l3", l3, hidden=not l3)

    def _render_led(self, st):
        sm = st["screen_mode"]
        if sm == 0:
            self._lines("Light", l1="Hue: %d" % st["hue"], l2="Brightness: %d" % st["brightness"],
                        l3="[ON] light " + ("off" if st["led_on"] else "on"))
        elif sm == 1:
            self._lines("Hue", big=str(st["hue"]), big_hidden=st["blink"] and not st["changing"])
        else:
            self._lines("Brightness", big=str(st["brightness"]),
                        big_hidden=st["blink"] and not st["changing"])

    def _render_song(self, st):
        self._lines("Song %d/%d" % (st["song_index"] + (1 if st["song_count"] else 0),
                                    st["song_count"]),
                    l1=st["song"][:25] or "(no songs on SD)",
                    l2="Playing" if st["playing"] else "Stopped",
                    l3="[ON] play / stop")

    def _render_settings(self, st):
        sm = st["screen_mode"]
        if sm == 0:
            self._lines("Settings", l1="[ADJUST] next page")
        elif sm == 1:
            self._lines("Volume", big=str(st["volume"]))
        elif sm == 2:
            self._lines("Contrast", big=str(st["contrast"]))
        elif sm == 3:
            self._lines("IP Address", l1=st["ip"] or "not connected",
                        l2=("AP: " + st["ap_ssid"]) if st["ap_mode"] else "")
        elif sm == 4:
            self._lines("Version", l1=NAME, l2=BOARD[:26])
        elif sm == 5:
            self._lines("Restart", l1="[OK] -> Restart Clock")
        else:
            self._lines("Firmware", l1="Update over USB:", l2="copy new files to", l3="CIRCUITPY")

    def _render_status(self, st):
        self.ic_alarm.show("on" if st["alarms_active"] else "off")
        self.ic_light.show("on" if st["led_on"] else None)
        self.ic_wifi.show("on" if st["wifi"] else "off")
        hidden = st["sd_ok"]
        if self.sd_label.hidden != hidden:
            self.sd_label.hidden = hidden
            self.dirty = True
        # Icons changing don't set dirty themselves; cheap enough to compare here.
        key = (self.ic_alarm.state, self.ic_light.state, self.ic_wifi.state)
        if key != getattr(self, "_icon_key", None):
            self._icon_key = key
            self.dirty = True
