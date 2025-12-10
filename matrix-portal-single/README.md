Single Matrix Display
=====================

Purpose
- Single-panel (64×32) Matrix Portal S3 display that shows one asset at a time, then cycles to the next.
- Reuses the same provisioning, Wi‑Fi, and API client as the multi‑panel scroller.
- Hard cut between assets with minimal flicker; 4‑color palette (black/white/green/red).

What’s Included
- code.py — single‑asset paging loop (user‑configurable dwell and order)
- api_client.py — HMAC v2 API client
- boot.py — A1 provision switch / factory reset
- wifimgr.py, provisioning_v2.py — local AP provisioning portal

Fonts & Libs
- Requires `fonts/spleen-8x16.bdf` on the device root. You can copy from the existing `CIRCUITPY/fonts/`.
- Requires the Adafruit CircuitPython libs in `/lib/` (same set used by the scroller).

Config
- Dwell time default is 2.5s; can be changed via `ITEM_DWELL_SEC` in `code.py`. Will prefer an API `item_dwell` setting when available.
- Asset order default: `['stocks','crypto','forex']` via `ASSET_ORDER` in `code.py`.

Deploy
1) Copy this folder’s contents to your device root (or rename folder to device root as needed).
2) Ensure `/lib/` contains: `adafruit_requests.mpy`, `adafruit_ticks.mpy`, `adafruit_bitmap_font/`, and RGB matrix deps.
3) Ensure `fonts/spleen-8x16.bdf` exists.
4) Provision: Hold A1 to GND and reset. Connect to `TickerSetup` and enter Wi‑Fi + PROV key.
5) Normal mode: Release A1 and reset.

Notes
- Heartbeat is sent periodically to keep device online.
- If no data is available, a simple "No Data" card is shown and the device retries fetches.

