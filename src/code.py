# Klever Klox - CircuitPython firmware entry point.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.
#
# Open the serial console (115200 baud, or Thonny / Mu / `circup`-friendly
# editors) to watch the boot log. Ctrl+C drops to the REPL.

from klever.app import App

App().run()
