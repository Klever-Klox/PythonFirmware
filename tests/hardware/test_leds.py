# Hardware test: WS2813 strip on GPIO5 (via the 330 ohm resistor).
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

import time

import neopixel

from klever import config

px = neopixel.NeoPixel(config.LED_PIN, config.NUM_LEDS, brightness=0.3, auto_write=False,
                       pixel_order=neopixel.GRB)
while True:
    for name, c in (("red", (255, 0, 0)), ("green", (0, 255, 0)), ("blue", (0, 0, 255))):
        print(name)
        px.fill(c)
        px.show()
        time.sleep(1)
    for i in range(config.NUM_LEDS):
        px.fill(0)
        px[i] = (255, 255, 255)
        px.show()
        time.sleep(0.1)
