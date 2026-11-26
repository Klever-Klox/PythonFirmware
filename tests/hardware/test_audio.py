# Hardware test: I2S amplifier. Plays a tone, then the first MP3 on the SD card.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

import array
import math
import time

import audiobusio
import audiocore

from klever import config, hardware
from klever.audio import Player, scan_songs

i2s = audiobusio.I2SOut(config.I2S_BCLK, config.I2S_LRC, config.I2S_DIN)
rate, n = 16000, 36
wave = array.array("h", [int(math.sin(2 * math.pi * i / n) * 8000) for i in range(n)])
tone = audiocore.RawSample(wave, sample_rate=rate)
print("440 Hz tone for 2 s...")
i2s.play(tone, loop=True)
time.sleep(2)
i2s.stop()
i2s.deinit()

spi = hardware.init_spi()
hardware.init_display(spi)
if hardware.init_sd(spi) is None:
    raise SystemExit("no SD card - tone test only")
songs = scan_songs(config.SD_MOUNT)
if not songs:
    raise SystemExit("no .mp3 files on the SD card")
p = Player(songs)
p.set_volume(40)
p.auto_next = False
p.play()
print("Playing", p.name, "for 20 s")
end = time.monotonic() + 20
while time.monotonic() < end and p.playing:
    p.update()
    time.sleep(0.05)
p.stop()
print("done")
