# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

import time

from . import config


def ms():
    """Milliseconds since boot. Integer maths, so it never loses precision."""
    return time.monotonic_ns() // 1_000_000


def log(*args):
    if config.DEBUG:
        print("[%d]" % ms(), *args)


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def wrap(v, n):
    """v modulo n, always non-negative; 0 when n <= 0 (e.g. no songs loaded)."""
    if n <= 0:
        return 0
    return v % n


def hsv_to_rgb(h, s, v):
    """FastLED-style HSV with all three channels 0-255."""
    if s == 0:
        return (v, v, v)
    region = h * 6 // 256
    rem = (h * 6) - region * 256
    p = (v * (255 - s)) >> 8
    q = (v * (255 - ((s * rem) >> 8))) >> 8
    t = (v * (255 - ((s * (255 - rem)) >> 8))) >> 8
    if region == 0:
        return (v, t, p)
    if region == 1:
        return (q, v, p)
    if region == 2:
        return (p, v, t)
    if region == 3:
        return (p, q, v)
    if region == 4:
        return (t, p, v)
    return (v, p, q)
