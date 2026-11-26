# WS2813 strip: manual light, colour presets, and the sunrise fade before alarms.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

import neopixel

from . import config
from .util import hsv_to_rgb

PRESETS = {
    "Red": (255, 0, 0),
    "Blue": (0, 0, 255),
    "Green": (0, 255, 0),
    "Yellow": (255, 255, 0),
    "Magenta": (255, 0, 255),
    "Cyan": (0, 255, 255),
    "White": (255, 255, 255),
}


class Leds:
    def __init__(self):
        self.px = neopixel.NeoPixel(config.LED_PIN, config.NUM_LEDS, brightness=1.0,
                                    auto_write=False, pixel_order=neopixel.GRB)
        self.rainbow = 0
        self.last = None

    def _fill(self, colour, hue, value, scale):
        n = config.NUM_LEDS
        if colour == "Rainbow":
            self.rainbow = (self.rainbow + 1) & 0xFF
            self.last = None
            for i in range(n):
                r, g, b = hsv_to_rgb((self.rainbow + i * 7) & 0xFF, 255, 255)
                self.px[i] = (r * scale // 255, g * scale // 255, b * scale // 255)
            return True
        if colour in PRESETS:
            r, g, b = PRESETS[colour]
        else:                                   # "Custom"
            r, g, b = hsv_to_rgb(hue, 255, value)
        c = (r * scale // 255, g * scale // 255, b * scale // 255)
        if c == self.last:
            return False
        self.last = c
        self.px.fill(c)
        return True

    def update(self, s, alarms, local, editing_led):
        """s = settings, local = struct_time, editing_led = LED screen is open."""
        minutes_to_alarm = config.LED_FADE_MINUTES + 1
        colour = s["colour"]
        if s["alarmsActive"] and s["fadeOn"]:
            today = (local.tm_wday + 1) % 7      # struct_time: Monday=0 -> Sunday=0
            now = local.tm_hour * 60 + local.tm_min
            for a in alarms:
                if not (a["active"] and a["fadeOn"] and a["days"][today]):
                    continue
                at = a["hour"] * 60 + a["minute"]
                diff = at - now + (1440 if now > at else 0)
                if diff <= minutes_to_alarm:
                    minutes_to_alarm = diff
                    colour = a["colour"]

        if s["LEDOn"]:
            changed = self._fill("Custom" if editing_led else colour, s["hue"],
                                 s["brightness"], config.LED_MAX_BRIGHTNESS)
        elif minutes_to_alarm <= config.LED_FADE_MINUTES:
            scale = (config.LED_FADE_MINUTES - minutes_to_alarm) * config.LED_MAX_BRIGHTNESS \
                // config.LED_FADE_MINUTES
            changed = self._fill(colour, s["hue"], s["brightness"], scale)
        else:
            changed = self.last != (0, 0, 0)
            self.last = (0, 0, 0)
            if changed:
                self.px.fill((0, 0, 0))
        if changed:
            self.px.show()
