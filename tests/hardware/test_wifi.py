# Hardware test: WiFi + NTP, using the credentials in /sd/settings.json.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

import time

from klever import hardware, tz
from klever.net import Net
from klever.settings import Settings

spi = hardware.init_spi()
hardware.init_display(spi)
hardware.init_sd(spi)
s = Settings()
s.load()
net = Net()
if not net.connect(s["ssid"], s["password"]):
    raise SystemExit("WiFi failed - check ssid/password in settings.json")
print("NTP:", net.sync_time(s["ntp"]))
zone = tz.Zone(s["zone"])
for _ in range(5):
    print("UTC  ", time.localtime())
    print("local", zone.local(time.time()))
    time.sleep(1)
