# Next Steps & Open Questions

- **Switch to delayed SIP feed:** Add a `STOCK_FEED` config defaulting to `delayed` for more accurate consolidated data (current feed is IEX). Wire through stock quote/daily bar calls; allow overrides (`iex`/`sip`).
- **Price sourcing summary:** Stocks/crypto now use latest quotes with daily bars for open/prev_close; change/% baseline prefers prev_close, falls back to open. Scheduler interval set to 15 minutes.
- **Weekend handling:** Daily bars fetched over the past ~10 days to ensure prev_close/open exist even on weekends/holidays; quotes older than today fall back to the latest daily close.
- **UI/Data:** Prev Close + Open are displayed; change/% uses prev_close when available. DB stores `prev_close` alongside open/last.
- **Potential enhancements:** Add intraday history table for last 15 minutes, configurable feed selection, and CLI/env overrides for interval/feed. Validate forex endpoint against Alpaca docs (current path is `/v2/forex/latest/rates`).

# Twelve Data forex budget (1 credit per symbol)
- Allowing up to 30 forex pairs: an hourly cadence (24 cycles/day) uses ~720 credits/day, under the 800/day cap.
- Respecting 8 credits/min: fetch in chunks of up to 8 pairs per cycle (e.g., 8+8+8+6 with short spacing) instead of all at once.

# Pi Zero 2W hub deployment (current session)
- Copied `alpaca-price-hub` onto the Pi (initially on boot; moved to `/opt/alpaca-price-hub`).
- Installed deps and created service scaffold: systemd unit `tickertronixhub.service` runs `main_web.py` via `/opt/alpaca-price-hub/.venv/bin/python3`; optional `/etc/tickertronix/.env` can set `HUB_LAN_IP`.
- Hub is reachable on LAN (confirmed via phone). mDNS host: `tickertronixhub.local:5001`.
- Matrix Portal still not pulling prices (likely hub URL/resolve issue on the device); needs follow-up to point `device_config.json` (or provisioning) to the Pi’s LAN IP/hostname and verify logs.
