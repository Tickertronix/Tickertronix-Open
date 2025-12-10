# Matrix Portal S3 – Local Hub Setup

## What’s different
- Talks to your local Hub (`/prices`), no cloud/HMAC/PROV keys.
- Provisioning collects Wi‑Fi + Hub URL (stored in `device_config.json` as `hub_base_url`).
- Fonts/scrolling logic unchanged; forex still scrolls if enabled on the Hub.

## Quick setup (fresh device)
1. Connect the Matrix Portal S3 via USB; it mounts as `CIRCUITPY`.
2. Delete old files if needed (keep `lib/` and fonts if you already have them).
3. Copy these files to `CIRCUITPY`: `code.py`, `api_client.py`, `provisioning_v2.py`, `wifimgr.py`, `fonts/`, `lib/`, optional `boot.py`.
4. Ensure `lib/` has: `adafruit_bitmap_font/`, `adafruit_display_text/`, `adafruit_requests.mpy`, `adafruit_ticks.mpy`, `adafruit_hashlib/`, `rgbmatrix` deps per Matrix Portal S3.

## Provisioning (Hub)
1. Boot with A1 grounded to enter setup.
2. Connect to AP `TickerSetup`; browse to `http://192.168.4.1`.
3. Enter Wi‑Fi SSID/password and Hub URL (e.g., `http://<hub-ip>:5001`). Submit.
4. Device saves `wifi.dat` and `device_config.json` (with `hub_base_url`), then reboots.

## Normal operation
- Reads `wifi.dat` + `device_config.json`, connects to Wi‑Fi, calls Hub `/prices`, and scrolls stocks/crypto/forex.
- Display settings default to single-line; adjust scroll speed/interval in `code.py` or extend `device_config.json` if desired.

## Resetting
- Delete `wifi.dat` and `device_config.json`, press RESET, then reprovision (A1 to GND).

## Power
- Matrix Portal S3: 5V via USB-C; LED matrix: stable 5V/4A for 64x32 panels.

## Troubleshooting
- No data: ensure Hub is running and `/prices` returns data; check Wi‑Fi/hub URL.
- Flicker/brightness: brightness capped in `code.py`; verify power supply for multi-panel rigs.
- Libraries missing: confirm required libs in `lib/`; check serial console for import errors.
