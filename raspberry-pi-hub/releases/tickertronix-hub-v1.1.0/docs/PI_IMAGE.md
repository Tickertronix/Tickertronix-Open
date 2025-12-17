# Tickertronix Hub Image (pi-gen)

How to flash and use the pi-gen-built image that ships with the hub preinstalled.

## What the image includes
- Raspberry Pi OS Lite (64-bit) with SSH enabled and hostname from the build config (defaults to `tickertronixhub`).
- Hub code in `/opt/tickertronix` with a Python venv and systemd unit `tickertronixhub.service` that runs `main_web.py` on boot.
- mDNS via Avahi (`http://tickertronixhub.local:8080` for the web UI, `:5001/health` for the API).

## Flash the image
1. Obtain the built archive (e.g., `tickertronix-hub-lite.zip`) and verify integrity: `sha256sum tickertronix-hub-lite.zip`.
2. Unzip: `unzip tickertronix-hub-lite.zip` (yields `...img`).
3. Write to an SD card:
   - **Raspberry Pi Imager (recommended):**
     - Open Imager → “Use custom” → pick `tickertronix-hub-lite.img`.
     - Click the gear icon (advanced options) and set:
       - Enable SSH.
       - Wi-Fi SSID/password/country.
       - Username/password (overrides the image default `tickertronix/tickertronix`).
       - Locale/timezone if desired.
     - Write the image.
   - **CLI dd** (manual alternative):
     ```bash
     # Replace /dev/sdX with your card device
     sudo dd if=tickertronix-hub-lite.img of=/dev/sdX bs=4M conv=fsync status=progress
     ```
4. Eject the card safely and insert it into the Pi.

## First boot
- Boot with Ethernet for easiest setup, or pre-set Wi-Fi in the pi-gen config (`WPA_ESSID/WPA_PSK`).
- Default login (unless the builder changed it in `config`): username `tickertronix`, password `tickertronix`. SSH to `ssh tickertronix@tickertronixhub.local` or use the Pi's IP.

**IMPORTANT**: Change the default password immediately after first login for security:
```bash
passwd
```
- Give the first boot a minute for filesystem resize and service startup. Check status with `sudo systemctl status tickertronixhub`.

## Configure the hub
1. Open the Web UI: `http://tickertronixhub.local:8080` (or `http://<pi-ip>:8080`).
2. Add Alpaca API keys on the credentials page, then select assets. The scheduler will auto-start once credentials exist.
3. Optional: set env vars (e.g., `TWELVE_DATA_API_KEY`) in `/opt/tickertronix/.env`, then restart the service:
   ```bash
   echo 'TWELVE_DATA_API_KEY=your-key' | sudo tee /opt/tickertronix/.env
   sudo systemctl restart tickertronixhub
   ```
4. Verify API health from another machine: `curl http://tickertronixhub.local:5001/health`.

## Updating and maintenance
- Pull latest code and dependencies:
  ```bash
  cd /opt/tickertronix
  sudo -u pi git pull
  sudo -u pi ./.venv/bin/pip install --no-cache-dir -r requirements.txt
  sudo systemctl restart tickertronixhub
  ```
- Logs: `journalctl -u tickertronixhub -f`.
- Change hostname: `sudo hostnamectl set-hostname <newname>` and reboot; update any URLs accordingly (Avahi will advertise `<newname>.local`).

If mDNS fails, reach the hub by IP or ensure `avahi-daemon` is running. Use `curl http://<pi-ip>:5001/prices` to confirm data access.

Tip for reliability: reserve the Pi's IP in your router and add a DNS A record for `tickertronixhub.local` pointing to it; optionally set `HUB_BASE_HOST` in `/opt/tickertronix/.env` and restart the service so the UI uses that deterministic name.
