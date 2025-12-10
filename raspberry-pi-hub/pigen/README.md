# Tickertronix Hub pi-gen Image

This folder adds a pi-gen stage and config to bake a reproducible Raspberry Pi OS Lite (64-bit) image with the hub preinstalled, running as a systemd service with mDNS enabled.

## What gets baked
- Raspberry Pi OS Lite (64-bit) with SSH enabled and hostname from `config` (default `tickertronixhub`).
- Avahi/mDNS so the box is reachable at `http://<hostname>.local`.
- Hub code in `/opt/tickertronix` cloned from `TICKERTRONIX_REPO_URL` at `TICKERTRONIX_REF`.
- Python venv under `/opt/tickertronix/.venv` with `requirements.txt` installed.
- Systemd service `tickertronixhub` (default) that runs `main_web.py` on boot; data/logs live in `/opt/tickertronix/data` and `/opt/tickertronix/logs`.

## Quick build (Docker)
1. Grab pi-gen (bookworm default): `git clone --depth=1 https://github.com/RPi-Distro/pi-gen.git`
2. Copy the config and stage into the pi-gen checkout:
   ```bash
   cp /path/to/raspberry-pi-hub/pigen/config pi-gen/config
   rsync -a /path/to/raspberry-pi-hub/pigen/stage-tickertronix pi-gen/
   ```
3. Pin what you want baked in (optional but recommended):
   ```bash
   export TICKERTRONIX_REF=$(cd /path/to/raspberry-pi-hub && git rev-parse HEAD)
   # Set per-build secrets/overrides:
   export FIRST_USER_PASS="changeme123"          # change on first boot
   export WPA_ESSID="YourWifiName" WPA_PSK="pass" WPA_COUNTRY="US"
   ```
4. Build: `cd pi-gen && sudo CLEAN=1 ./build-docker.sh` (use `./build.sh` for native builds).
5. Artifacts land in `deploy/` (e.g., `tickertronix-hub-lite.zip` with the `.img` inside). Grab the SHA: `sha256sum deploy/*.zip`.

## Config knobs (pigen/config)
- `IMG_NAME`, `HOSTNAME`, `ENABLE_SSH`, `TARGET_ARCH=arm64`, `STAGE_LIST="stage0 stage1 stage2 stage-tickertronix"` (Lite-only; add stage3/4 if you want desktop packages).
- `FIRST_USER_NAME`/`FIRST_USER_PASS` set the default login (override via env when building; change immediately after first boot).
- Wi-Fi preconfig (optional): `WPA_ESSID`, `WPA_PSK`, `WPA_COUNTRY`.
- Hub settings: `TICKERTRONIX_REPO_URL`, `TICKERTRONIX_REF` (branch/tag/commit), `TICKERTRONIX_INSTALL_DIR` (`/opt/tickertronix`), `TICKERTRONIX_SERVICE_NAME` (`tickertronixhub`), `TICKERTRONIX_SERVICE_USER` (`pi`).
- `DEPLOY_ZIP=1` zips the image; drop it or set `COMPRESS=xz` if you prefer `.img.xz`.

Re-run with `CLEAN=1` to discard any cached rootfs between builds.
