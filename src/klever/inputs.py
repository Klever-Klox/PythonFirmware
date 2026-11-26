# Touch pads, rotary encoder and the encoder's push switch, turned into events.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.
#
# Nothing here blocks: the Arduino firmware spun in while-loops waiting for a
# pad to be released, which froze the screen and starved the audio.

import digitalio
import rotaryio
import touchio

from . import config
from .util import log, ms

MODE, ADJ, ON, OK = "MODE", "ADJUST", "ON", "OK"


class Pad:
    def __init__(self, name, pin):
        self.name = name
        self.ok = True
        self.down = False
        self.since = 0
        try:
            self.t = touchio.TouchIn(pin)
        except Exception as e:
            log("[TOUCH] %s pad unavailable: %s" % (name, e))
            self.t = None
            self.ok = False

    def raw(self):
        return self.t.raw_value if self.t else 0

    def pressed(self):
        return self.ok and self.raw() > config.TOUCH_THRESHOLD


class Inputs:
    def __init__(self):
        self.pads = [Pad(MODE, config.TOUCH_MODE), Pad(ADJ, config.TOUCH_ADJ),
                     Pad(ON, config.TOUCH_ON), Pad(OK, config.TOUCH_OK)]
        self.enc = rotaryio.IncrementalEncoder(config.ENC_A, config.ENC_B,
                                               divisor=config.ENC_DIVISOR)
        self.last_pos = self.enc.position
        self.last_turn = 0
        self.sw = digitalio.DigitalInOut(config.ENC_SW)
        self.sw.switch_to_input(pull=digitalio.Pull.UP)
        self.sw_down = False
        self.sw_since = 0
        self.sw_fired = False
        self.adj_fired = False
        self._debug_at = 0
        self._probe()

    def _probe(self):
        # Nobody touches the clock while it boots, so a pad that already reads
        # "pressed" is unwired or shorted: ignore it instead of acting on it.
        for p in self.pads:
            if p.ok and p.pressed():
                p.ok = False
                log("[TOUCH] ERROR: %s pad reads pressed at boot (raw %d) - disabled"
                    % (p.name, p.raw()))
        if self.all_ok:
            log("[TOUCH] all 4 pads OK")

    @property
    def all_ok(self):
        return all(p.ok for p in self.pads)

    def poll(self):
        """Returns a list of events:
        ("press", pad)        pad went down
        ("release", pad, held_ms)
        ("hold", pad)         ADJUST held for ADJ_HOLD_MS (fires once)
        ("turn", steps)       encoder moved, with acceleration applied
        ("knob", "click")     encoder switch released before the restart hold
        ("knob", "hold")      encoder switch held for KNOB_RESTART_MS
        """
        now = ms()
        ev = []

        for p in self.pads:
            down = p.pressed()
            if down and not p.down:
                p.down, p.since = True, now
                if p.name == ADJ:
                    self.adj_fired = False
                ev.append(("press", p.name))
            elif down and p.down:
                held = now - p.since
                if p.name == ADJ and not self.adj_fired and held >= config.ADJ_HOLD_MS:
                    self.adj_fired = True
                    ev.append(("hold", ADJ))
                if held >= config.TOUCH_STUCK_MS:
                    p.ok, p.down = False, False
                    log("[TOUCH] %s pad stuck for %ds - disabled" % (p.name, held // 1000))
            elif not down and p.down:
                p.down = False
                ev.append(("release", p.name, now - p.since))

        pos = self.enc.position
        if pos != self.last_pos:
            delta = pos - self.last_pos
            self.last_pos = pos
            dt = now - self.last_turn
            self.last_turn = now
            ev.append(("turn", delta * (3 if dt < 40 else 2 if dt < 70 else 1)))

        sw = not self.sw.value
        if sw and not self.sw_down:
            self.sw_down, self.sw_since, self.sw_fired = True, now, False
        elif sw and not self.sw_fired and now - self.sw_since >= config.KNOB_RESTART_MS:
            self.sw_fired = True
            ev.append(("knob", "hold"))
        elif not sw and self.sw_down:
            self.sw_down = False
            if not self.sw_fired and now - self.sw_since > 30:   # 30 ms debounce
                ev.append(("knob", "click"))

        if config.DEBUG_TOUCH and now - self._debug_at > 500:
            self._debug_at = now
            print("[TOUCH] " + "  ".join("%s=%d%s" % (p.name, p.raw(), "" if p.ok else "(off)")
                                         for p in self.pads))
        return ev
