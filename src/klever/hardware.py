# Brings up the one shared SPI bus, then the TFT and the SD card on it.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

import busio
import displayio
import sdcardio
import storage

try:                                   # CircuitPython 9+
    from fourwire import FourWire
except ImportError:                    # CircuitPython 8
    from displayio import FourWire

from adafruit_st7735r import ST7735R

from . import config
from .util import log


def init_spi():
    displayio.release_displays()
    return busio.SPI(config.SPI_SCK, MOSI=config.SPI_MOSI, MISO=config.SPI_MISO)


def init_display(spi):
    bus = FourWire(spi, command=config.TFT_DC, chip_select=config.TFT_CS,
                   reset=config.TFT_RST, baudrate=config.TFT_BAUDRATE)
    if config.SCREEN_TYPE == "green":
        kwargs = dict(colstart=2, rowstart=1, bgr=False)
    else:
        kwargs = dict(bgr=True)
    display = ST7735R(bus, width=160, height=128, rotation=90,
                      backlight_pin=config.TFT_BL, brightness=1.0, **kwargs)
    # Refresh only when we ask: an automatic refresh in the middle of an MP3
    # read would hold the shared bus and make the audio stutter.
    display.auto_refresh = False
    return display


def init_sd(spi):
    try:
        sd = sdcardio.SDCard(spi, config.SD_CS, baudrate=config.SD_BAUDRATE)
        storage.mount(storage.VfsFat(sd), config.SD_MOUNT)
        log("[SD] mounted at", config.SD_MOUNT)
        return sd
    except (OSError, ValueError) as e:
        log("[SD] ERROR: no SD card (%s) - settings and audio disabled" % e)
        return None
