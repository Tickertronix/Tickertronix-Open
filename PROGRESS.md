# Progress Notes

## Hub
- Fixed `db.py` indentation issue; `devices` and `device_settings` tables now migrate/create correctly (dwell_seconds and asset_order columns added).
- API validates dwell_seconds (1–30s) and asset_order (stocks/crypto/forex). Device type preserved on registration/heartbeat.
- Devices page: scroll vs single fields are conditionally shown. Scroll-mode naming fixed so settings persist. Added dwell seconds and asset order inputs; Force Refresh bumps settings timestamp.

## Matrix Portal – Scrolling (matrix-portal-scroll)
- Local hub client restored (no HMAC), heartbeat every ~2 minutes, settings version tracking. Price fetch interval uses hub `update_interval`.
- Provisioning unchanged; device_key/device_type set in config. Heartbeats send `device_type=matrix_portal_scroll`.

## Matrix Portal – Single Panel (matrix-portal-single)
- Swapped to a local hub client (api_client.py) with heartbeat, settings fetch (brightness, update_interval, dwell_seconds, asset_order), and ticker parsing.
- code.py now uses LocalHubAPI (no HMAC), heartbeat ~120s, applies dwell/order from hub settings; device_key generation only during provisioning.
- Provisioning updated to collect Wi-Fi, hub URL, optional device key (auto-generates), and saves `device_type=matrix_portal_single`.
- Remaining: optional cleanup of old orphaned/HMAC logs (they’re inert with the local client).

## Deployment/Recovery Notes
- If missing tables/errors: run `Database()` on the Pi to initialize and restart `tickertronixhub.service`. Confirm tables: config, selected_assets, asset_prices, devices, device_settings.
- Push code via `rsync` to `/opt/alpaca-price-hub`, then `sudo systemctl restart tickertronixhub.service`.
- If provisioning is needed, ground A1, fill Wi-Fi + hub URL (device key optional), then unground and reset. Alternatively, preseed `wifi.dat` and `device_config.json` with `device_key` and `hub_base_url`.

## Known Good Behavior
- Hub up after power cycle; DB tables exist.
- Devices page shows only relevant fields per device type.
- Scroll device registers and pulls settings; single-panel firmware partially verified (requires libs on board).

