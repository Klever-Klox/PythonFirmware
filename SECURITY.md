# Security policy

## Supported versions

Only the latest release receives security fixes.

| Version   | Supported |
|-----------|-----------|
| 1.0.x.x   | Yes       |
| < 1.0     | No        |

## Reporting a vulnerability

Please **do not open a public issue** for a security problem.

Report it privately through GitHub instead: on this repository, open
**Security → Report a vulnerability**. Include:

- the firmware version (shown on the clock under *Settings → Version*),
- what an attacker can do and what they need (same WiFi network, physical access, …),
- steps to reproduce.

You should get an acknowledgement within 7 days. Please give us a reasonable
time to release a fix before you disclose anything publicly.

## Known limitations (by design in 1.0.0.0)

These are documented limitations rather than bugs. They are on the roadmap:

- **The local web page has no login.** Anyone on the same WiFi network can change
  settings and alarms at `http://kleverklox.local`. Only connect the clock to a
  network you trust.
- **The first-time setup access point (`Klever_Klox`) is open**, without a password,
  while the clock has no WiFi credentials. It is only active until WiFi is set up.
- **WiFi credentials are stored in plain text** in `settings.json` on the SD card.
  Anyone who can take the card out can read them.
- **Firmware updates are by USB only.** There is no over-the-air update, so there
  is no remote code-update path to attack.
