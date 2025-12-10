# Matrix Portal S3 – Local Hub Firmware

CircuitPython firmware for the Matrix Portal S3 scrolling ticker, now talking to the local Hub (no cloud auth).

## What changed
- Uses the Hub’s `/prices` endpoint via `LocalHubAPI` (no HMAC/provisioning keys).
- Provisioning collects Wi‑Fi + Hub URL; no PROV keys. Saves `wifi.dat` and `device_config.json` with `hub_base_url`.
- Forex still scrolls if enabled on the Hub (hourly via Twelve Data on the Hub).
- Scrolling logic, fonts, and display settings remain intact.

## Quick start
1) Copy this folder to your Matrix Portal S3 `CIRCUITPY` drive.
2) For first-time setup: hold A1 to GND on boot to enter provisioning.
   - Connect to AP `TickerSetup`, browse to `http://192.168.4.1`.
   - Enter Wi‑Fi SSID/password and your Hub URL (e.g., `http://<hub-ip>:5001`).
   - Device saves config and reboots.
3) Normal run:
   - Reads `wifi.dat` and `device_config.json` (hub_base_url).
   - Connects to Wi‑Fi and pulls `/prices` from the Hub; scrolls stocks/crypto/forex.

## Files
- `code.py` – Main firmware (scrolling).
- `api_client.py` – LocalHubAPI client (maps `/prices` to display data).
- `provisioning_v2.py` – Wi‑Fi + Hub URL portal.
- `wifimgr.py` – Wi‑Fi manager; provisioning flag is `hub_base_url`.
- `fonts/`, `lib/` – Fonts and CircuitPython deps.

## Notes
- Brightness capped for multi-panel rigs.
- Fonts: `fonts/spleen-16x32.bdf` (single), `fonts/spleen-8x16.bdf` (dual).
- Scroll speed/interval tunable in `code.py`; display settings can also be extended via `device_config.json`.
