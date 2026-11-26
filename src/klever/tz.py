# Minimal POSIX TZ support, so settings.json keeps the same "zone" string the
# Arduino firmware used (e.g. Ireland: "IST-1GMT0,M10.5.0,M3.5.0/1").
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.
#
# Supports: STD offset [DST [offset] [,Mm.w.d[/time],Mm.w.d[/time]]]
# The hardware RTC always holds UTC; this converts to local time on demand.

import time

_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def days_in_month(y, m):
    return 29 if (m == 2 and is_leap(y)) else _DAYS[m - 1]


def _days_from_civil(y, m, d):
    """Days since 1970-01-01 (Howard Hinnant's algorithm, no time.mktime needed)."""
    y -= m <= 2
    era = (y if y >= 0 else y - 399) // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def epoch(y, m, d, hh=0, mm=0, ss=0):
    return _days_from_civil(y, m, d) * 86400 + hh * 3600 + mm * 60 + ss


def weekday_sun0(y, m, d):
    """0 = Sunday ... 6 = Saturday (the index alarm 'days' arrays use)."""
    return (_days_from_civil(y, m, d) + 4) % 7   # 1970-01-01 was a Thursday


class Zone:
    def __init__(self, spec):
        self.spec = spec or "UTC0"
        self.std_offset = 0        # seconds east of UTC
        self.dst_offset = None
        self.start = None          # (month, week, wday, seconds)
        self.end = None
        try:
            self._parse(self.spec)
        except Exception as e:     # a bad string must never stop the clock
            print("[TZ] could not parse %r (%s) - using UTC" % (spec, e))
            self.std_offset, self.dst_offset, self.start, self.end = 0, None, None, None

    # ---- parsing ----
    def _parse(self, s):
        i = self._name(s, 0)
        off, i = self._offset(s, i)
        self.std_offset = -off                  # POSIX offsets are west-positive
        if i >= len(s):
            return
        i = self._name(s, i)
        self.dst_offset = self.std_offset + 3600
        if i < len(s) and s[i] != ",":
            off, i = self._offset(s, i)
            self.dst_offset = -off
        if i < len(s) and s[i] == ",":
            rules = s[i + 1:].split(",")
            self.start = self._rule(rules[0])
            self.end = self._rule(rules[1])
        else:                                   # EU-style default if no rules given
            self.start = (3, 5, 0, 3600)
            self.end = (10, 5, 0, 7200)

    @staticmethod
    def _name(s, i):
        if s[i] == "<":
            return s.index(">", i) + 1
        while i < len(s) and s[i].isalpha():
            i += 1
        return i

    @staticmethod
    def _offset(s, i):
        sign = 1
        if s[i] in "+-":
            sign = -1 if s[i] == "-" else 1
            i += 1
        j = i
        while j < len(s) and (s[j].isdigit() or s[j] == ":"):
            j += 1
        parts = [int(p) for p in s[i:j].split(":")]
        secs = parts[0] * 3600
        if len(parts) > 1:
            secs += parts[1] * 60
        if len(parts) > 2:
            secs += parts[2]
        return sign * secs, j

    @staticmethod
    def _rule(r):
        if not r.startswith("M"):
            raise ValueError("only Mm.w.d rules are supported")
        when = 7200
        if "/" in r:
            r, t = r.split("/")
            neg = t.startswith("-")
            hms = [int(p) for p in t.lstrip("+-").split(":")]
            when = hms[0] * 3600 + (hms[1] * 60 if len(hms) > 1 else 0) + (hms[2] if len(hms) > 2 else 0)
            if neg:
                when = -when
        m, w, d = [int(p) for p in r[1:].split(".")]
        return (m, w, d, when)

    # ---- conversion ----
    @staticmethod
    def _rule_day(year, rule):
        m, w, d, _ = rule
        first = weekday_sun0(year, m, 1)
        day = 1 + (d - first) % 7 + (w - 1) * 7
        last = days_in_month(year, m)
        while day > last:
            day -= 7
        return epoch(year, m, day)

    def offset_at(self, utc):
        """Seconds to add to a UTC timestamp to get local time."""
        if self.dst_offset is None or self.start is None:
            return self.std_offset
        year = time.localtime(utc + self.std_offset).tm_year
        start = self._rule_day(year, self.start) + self.start[3] - self.std_offset
        end = self._rule_day(year, self.end) + self.end[3] - self.dst_offset
        if start < end:
            in_dst = start <= utc < end
        else:                                   # southern hemisphere / Ireland-style
            in_dst = not (end <= utc < start)
        return self.dst_offset if in_dst else self.std_offset

    def local(self, utc):
        return time.localtime(utc + self.offset_at(utc))

    def to_utc(self, local_epoch):
        # Good to the hour at the two transition instants a year - fine for a clock.
        return local_epoch - self.offset_at(local_epoch - self.std_offset)
