# Raspberry Pi Zero 2 W Deployment (Local Hub)

This sets up the hub to run headless on a Pi (Zero 2 W friendly) and be reachable at `http://tickertronixhub.local:5001/prices` (or your LAN IP). Keep the canonical name for embedded clients; use router DNS/DHCP to make it deterministic.

## Quick Install
```bash
sudo ./scripts/setup_pi.sh   # defaults to hostname tickertronixhub
```
Recommended for reliability:
- Reserve the Pi’s IP in your router (DHCP reservation).
- Add a DNS A record on your router: `tickertronixhub.local` (or `.lan`) → that IP.
- Optionally set `/opt/tickertronix/.env` with `HUB_BASE_HOST=tickertronixhub.local` so UI links use the deterministic name; restart the service.
What it does:
- Installs deps: git, python3-venv/pip, avahi-daemon (mDNS).
- Clones/updates repo into `/opt/tickertronix` (uses `main` by default).
- Creates venv and installs `requirements.txt`.
- Installs systemd unit `tickertronixhub.service` to run `python3 main_web.py` on boot.
- Enables and starts the service.

After install:
- Test from another device: `curl http://tickertronixhub.local:5001/prices` (or use the Pi’s LAN IP).
- For updates: `cd /opt/tickertronix && git pull && source .venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart tickertronixhub`.

## Config
- Env file (optional): `/opt/tickertronix/.env` is loaded by systemd if present; set `HUB_BASE_HOST=tickertronixhub.local` (or your DNS/DHCP name or fixed IP), `TWELVE_DATA_API_KEY`, etc.
- Port/host: defaults are `0.0.0.0:5001` (config.py). Firewall must allow TCP/5001.
- mDNS: Avahi is installed/enabled; hostname defaults to `tickertronixhub`. For deterministic resolution, reserve the IP in your router, add a DNS A record for `tickertronixhub.local` (or `.lan`), and set `HUB_BASE_HOST` in `.env`.

## Matrix Portal Provisioning
- Use the hub URL: `http://tickertronixhub.local:5001` (or `http://<pi-lan-ip>:5001`).
- Provision on the Matrix Portal (A1 grounded or auto-provision) via the `TickerSetup` AP at `http://192.168.4.1`, entering Wi‑Fi and the hub URL.
- Alternatively, drop `device_config.json` on CIRCUITPY with `{"hub_base_url": "http://<pi-lan-ip>:5001"}`.

## Troubleshooting
- Service: `sudo systemctl status tickertronixhub`.
- Logs: `journalctl -u tickertronixhub -f`.
- mDNS: `ping tickertronixhub.local`; if it fails, use the Pi’s IP or ensure Avahi is running. For zero-collision access, use the DNS A record and `HUB_BASE_HOST`.
- Port: ensure firewall allows TCP/5001. Use `curl http://<pi-ip>:5001/health`.
