# Hardware test: touch pads (raw readings), rotary encoder and its switch.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

import time

from klever import config
from klever.inputs import Inputs

config.DEBUG_TOUCH = True                       # print raw touch readings twice a second
inp = Inputs()
print("Touch each pad, turn and press the knob. Threshold:", config.TOUCH_THRESHOLD)
pos = 0
while True:
    for ev in inp.poll():
        if ev[0] == "turn":
            pos += ev[1]
            print("turn", ev[1], "-> position", pos)
        else:
            print(*ev)
    time.sleep(0.01)
