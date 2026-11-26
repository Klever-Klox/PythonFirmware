# Desktop test for the POSIX TZ parser: python -m unittest discover -s tests
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

import os
import sys
import time
import unittest

# CircuitPython has no host time zone: localtime() == gmtime(). Match that here.
time.localtime = time.gmtime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "klever"))
import tz  # noqa: E402

IRELAND = "IST-1GMT0,M10.5.0,M3.5.0/1"


class TzTest(unittest.TestCase):
    def test_epoch_matches_calendar(self):
        import calendar
        for y, m, d in ((1970, 1, 1), (2000, 2, 29), (2026, 11, 25), (2038, 1, 19)):
            self.assertEqual(tz.epoch(y, m, d), calendar.timegm((y, m, d, 0, 0, 0)))

    def test_weekday(self):
        self.assertEqual(tz.weekday_sun0(2026, 11, 25), 3)   # Wednesday
        self.assertEqual(tz.weekday_sun0(2026, 3, 29), 0)    # Sunday

    def test_ireland(self):
        z = tz.Zone(IRELAND)
        self.assertEqual(z.offset_at(tz.epoch(2026, 1, 15, 12)), 0)        # winter: GMT
        self.assertEqual(z.offset_at(tz.epoch(2026, 7, 15, 12)), 3600)     # summer: IST
        # 2026: clocks go forward Sun 29 Mar 01:00 UTC, back Sun 25 Oct 01:00 UTC
        self.assertEqual(z.offset_at(tz.epoch(2026, 3, 29, 0, 59)), 0)
        self.assertEqual(z.offset_at(tz.epoch(2026, 3, 29, 1, 0)), 3600)
        self.assertEqual(z.offset_at(tz.epoch(2026, 10, 25, 0, 59)), 3600)
        self.assertEqual(z.offset_at(tz.epoch(2026, 10, 25, 1, 0)), 0)

    def test_us_eastern(self):
        z = tz.Zone("EST5EDT,M3.2.0,M11.1.0")
        self.assertEqual(z.offset_at(tz.epoch(2026, 1, 1)), -5 * 3600)
        self.assertEqual(z.offset_at(tz.epoch(2026, 7, 1)), -4 * 3600)

    def test_round_trip(self):
        z = tz.Zone(IRELAND)
        local = tz.epoch(2026, 7, 1, 9, 30)
        self.assertEqual(z.local(z.to_utc(local)).tm_hour, 9)

    def test_bad_string_falls_back_to_utc(self):
        self.assertEqual(tz.Zone("garbage,,").offset_at(0), 0)
        self.assertEqual(tz.Zone("").offset_at(0), 0)


if __name__ == "__main__":
    unittest.main()
