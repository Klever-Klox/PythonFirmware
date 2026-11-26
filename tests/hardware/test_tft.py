# Hardware test: TFT on the shared SPI bus, plus the backlight.
# Copy to CIRCUITPY as code.py (keep the klever/ folder there too).
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

import time

import displayio
import terminalio
import vectorio
from adafruit_display_text.label import Label

from klever import hardware

spi = hardware.init_spi()
display = hardware.init_display(spi)
g = displayio.Group()
for i, c in enumerate((0xFF0000, 0x00FF00, 0x0000FF, 0xFFFFFF)):
    p = displayio.Palette(1)
    p[0] = c
    g.append(vectorio.Rectangle(pixel_shader=p, width=40, height=96, x=i * 40, y=0))
g.append(Label(terminalio.FONT, text="R  G  B  W  - TFT OK?", color=0xFFFFFF, x=4, y=110))
display.root_group = g
display.refresh(target_frames_per_second=None)
print("Expect red, green, blue, white bars left to right.")
print("If red and blue are swapped, set SCREEN_TYPE in klever/config.py.")

while True:
    for level in (1.0, 0.5, 0.1, 0.0, 1.0):
        print("backlight", level)
        display.brightness = level
        time.sleep(1.5)
    print("If the brightness never changed, BL is not wired to GPIO11.")
