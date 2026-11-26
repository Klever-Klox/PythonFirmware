# WiFi station / access point, NTP time sync and mDNS.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

import rtc
import socketpool
import wifi

from . import config
from .util import log

try:
    import mdns
except ImportError:
    mdns = None


class Net:
    def __init__(self):
        self.pool = None
        self.connected = False
        self.ap_mode = False
        self.ip = ""
        self._mdns = None

    def connect(self, ssid, password):
        if not ssid:
            log("[WIFI] no saved network")
            return False
        log("[WIFI] connecting to", ssid)
        try:
            wifi.radio.hostname = config.MDNS_HOSTNAME
            wifi.radio.connect(ssid, password or None, timeout=10)
        except Exception as e:                 # ConnectionError, wrong password, etc.
            log("[WIFI] failed:", e)
            self.connected = False
            return False
        self.connected = True
        self.ip = str(wifi.radio.ipv4_address)
        self.pool = socketpool.SocketPool(wifi.radio)
        log("[WIFI] connected, IP", self.ip)
        self._start_mdns()
        return True

    def check(self):
        self.connected = wifi.radio.connected if not self.ap_mode else False
        return self.connected

    def start_ap(self):
        log("[WIFI] starting access point", config.AP_SSID)
        try:
            wifi.radio.start_ap(config.AP_SSID)          # open network, like v2.x
        except Exception as e:
            log("[WIFI] could not start AP:", e)
            return False
        self.ap_mode = True
        self.ip = str(wifi.radio.ipv4_address_ap)
        self.pool = socketpool.SocketPool(wifi.radio)
        log("[WIFI] AP up - join '%s' and browse to http://%s" % (config.AP_SSID, self.ip))
        self._start_mdns()
        return True

    def _start_mdns(self):
        if mdns is None or self._mdns is not None:
            return
        try:
            self._mdns = mdns.Server(wifi.radio)
            self._mdns.hostname = config.MDNS_HOSTNAME
            self._mdns.advertise_service(service_type="_http", protocol="_tcp", port=80)
            log("[WIFI] mDNS: http://%s.local" % config.MDNS_HOSTNAME)
        except Exception as e:
            log("[WIFI] mDNS failed:", e)

    def sync_time(self, server):
        """Set the RTC to UTC from NTP. Returns True on success."""
        if not self.connected:
            return False
        try:
            import adafruit_ntp
            ntp = adafruit_ntp.NTP(self.pool, server=server or "pool.ntp.org",
                                   tz_offset=0, socket_timeout=5)
            rtc.RTC().datetime = ntp.datetime
            log("[NTP] time set from", server)
            return True
        except Exception as e:
            log("[NTP] failed:", e)
            return False
