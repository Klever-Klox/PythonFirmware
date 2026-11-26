# Hardware test: microSD card on the shared SPI bus (with the TFT also attached).
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

import os

from klever import config, hardware
from klever.audio import scan_songs

spi = hardware.init_spi()
display = hardware.init_display(spi)          # bring the TFT up too: proves bus sharing
if hardware.init_sd(spi) is None:
    raise SystemExit("SD card FAILED - check CS=GPIO34, MISO=GPIO37, card formatted FAT32")

print("Root:", os.listdir(config.SD_MOUNT))
path = config.SD_MOUNT + "/kk_test.txt"
with open(path, "w") as f:
    f.write("hello")
with open(path) as f:
    assert f.read() == "hello"
os.remove(path)
print("Write/read OK")
songs = scan_songs(config.SD_MOUNT)
print("%d MP3 files:" % len(songs))
for name, full in songs[:20]:
    print("  ", full)
