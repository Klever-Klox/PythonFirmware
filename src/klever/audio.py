# MP3 playback from the SD card through the MAX98357A.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

import os

import audiobusio
import audiomixer
import audiomp3

from . import config
from .util import log, wrap


def scan_songs(root):
    """Every .mp3 on the card, sorted, as (display name, full path)."""
    found = []

    def walk(path):
        try:
            entries = os.listdir(path)
        except OSError:
            return
        for name in entries:
            if name.startswith("."):
                continue                       # macOS ._ files and friends
            full = path + "/" + name
            try:
                is_dir = os.stat(full)[0] & 0x4000
            except OSError:
                continue
            if is_dir:
                walk(full)
            elif name.lower().endswith(".mp3"):
                found.append((name, full))

    walk(root)
    found.sort(key=lambda s: s[0].lower())
    return found


class Player:
    def __init__(self, songs):
        self.songs = songs
        self.index = 0
        self.volume = 100
        self.auto_next = True
        self.playing = False
        self.i2s = audiobusio.I2SOut(config.I2S_BCLK, config.I2S_LRC, config.I2S_DIN)
        self.decoder = None
        self.mixer = None
        self._file = None

    # ---- selection ----
    @property
    def count(self):
        return len(self.songs)

    @property
    def name(self):
        return self.songs[self.index][0] if self.songs else ""

    def select_name(self, name):
        for i, (n, _) in enumerate(self.songs):
            if n == name:
                self.index = i
                return True
        return False

    def step(self, delta):
        self.index = wrap(self.index + delta, self.count)
        if self.playing:
            self.play()
        return self.name

    # ---- transport ----
    def play(self):
        if not self.songs:
            log("[AUDIO] no songs on the SD card")
            return False
        path = self.songs[self.index][1]
        try:
            f = open(path, "rb")
        except OSError as e:
            log("[AUDIO] cannot open", path, e)
            return False
        self.i2s.stop()
        if self._file:
            self._file.close()
        self._file = f
        try:
            if self.decoder is None:
                self.decoder = audiomp3.MP3Decoder(f)
            else:
                self.decoder.file = f
        except Exception as e:                 # corrupt / non-MP3 file
            log("[AUDIO] decode error in", path, e)
            self.playing = False
            return False
        rate, ch = self.decoder.sample_rate, self.decoder.channel_count
        if (self.mixer is None or self.mixer.sample_rate != rate
                or getattr(self, "_mixer_ch", None) != ch):
            self.mixer = audiomixer.Mixer(voice_count=1, sample_rate=rate, channel_count=ch,
                                          bits_per_sample=16, samples_signed=True,
                                          buffer_size=8192)
            self._mixer_ch = ch
        self.set_volume(self.volume)
        self.i2s.play(self.mixer)
        self.mixer.voice[0].play(self.decoder)
        self.playing = True
        log("[AUDIO] playing", self.name)
        return True

    def stop(self):
        self.playing = False
        self.i2s.stop()
        if self._file:
            self._file.close()
            self._file = None

    def set_volume(self, percent):
        self.volume = percent
        if self.mixer:
            self.mixer.voice[0].level = percent / 100

    def update(self):
        """Call every loop. Returns True if the track changed by itself."""
        if self.playing and self.mixer and not self.mixer.voice[0].playing:
            if self.auto_next and self.count > 1:
                self.index = wrap(self.index + 1, self.count)
                self.play()
                return True
            if self.auto_next:
                self.play()                    # single song: loop it
                return False
            self.stop()
            return True
        return False
