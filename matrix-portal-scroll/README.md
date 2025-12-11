# Matrix Portal S3 – Local Hub Firmware

CircuitPython firmware for the Matrix Portal S3 scrolling ticker, now talking to the local Hub (no cloud auth).

![Matrix Portal Scroll demo](../assets/matrix-portal-scroll/demo.jpg)

## What changed
- Uses the Hub’s `/prices` endpoint via `LocalHubAPI` (no HMAC/provisioning keys).
- Provisioning collects Wi‑Fi + Hub URL; no PROV keys. Saves `wifi.dat` and `device_config.json` with `hub_base_url`.
- Forex still scrolls if enabled on the Hub (hourly via Twelve Data on the Hub).
- Scrolling logic, fonts, and display settings remain intact.

## Quick start
1) Flash CircuitPython on the Matrix Portal S3  
   - Download UF2 for Matrix Portal S3: https://circuitpython.org/board/matrixportal_s3/  
   - Double-tap RESET to enter bootloader (`RPI-RP2` drive), drag UF2, wait for `CIRCUITPY` to appear.
2) Copy firmware files  
   - Easiest: download the latest `matrix-portal-scroll.zip` from GitHub Releases (or build with `./scripts/build_matrix_portal_releases.sh`), then unzip onto `CIRCUITPY` (keeps `lib/` + `fonts/` intact).  
   - Manual: copy `code.py`, `api_client.py`, `provisioning_v2.py`, `wifimgr.py`, `fonts/`, and required `lib/` deps to `CIRCUITPY`.
3) First-time provisioning  
   - Hold A1 to GND on boot to enter provisioning.  
   - Connect to AP `TickerSetup`, browse to `http://192.168.4.1`.  
   - Enter Wi‑Fi + Hub URL (e.g., `http://<hub-ip>:5001`). Device saves config and reboots.
4) Normal run  
   - Reads `wifi.dat` and `device_config.json` (`hub_base_url`), connects to Wi‑Fi, pulls `/prices`, and scrolls stocks/crypto/forex.

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
