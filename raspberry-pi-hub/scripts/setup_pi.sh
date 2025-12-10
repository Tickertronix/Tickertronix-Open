#!/usr/bin/env bash
# Bootstrap script for running Raspberry Pi Hub on a Raspberry Pi (Zero 2 W friendly).
# - Installs dependencies
# - Creates/updates venv
# - Installs systemd service to run main_web.py on boot
# Usage: sudo ./scripts/setup_pi.sh [--hostname tickertronixhub] [--repo-url <url>] [--branch <branch>]

set -euo pipefail

HOSTNAME_OVERRIDE=""
REPO_URL="https://github.com/tickertronix/alpaca-price-hub.git"
BRANCH="main"
INSTALL_DIR="/opt/tickertronix"
SERVICE_NAME="tickertronixhub"
PY_BIN="python3"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hostname)
      HOSTNAME_OVERRIDE="$2"; shift 2;;
    --repo-url)
      REPO_URL="$2"; shift 2;;
    --branch)
      BRANCH="$2"; shift 2;;
    *)
      echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root (sudo)."
  exit 1
fi

echo "[INFO] Updating apt and installing packages..."
apt-get update -y
apt-get install -y git python3-venv python3-pip avahi-daemon

if [[ -n "$HOSTNAME_OVERRIDE" ]]; then
  echo "[INFO] Setting hostname to $HOSTNAME_OVERRIDE"
  hostnamectl set-hostname "$HOSTNAME_OVERRIDE"
fi

echo "[INFO] Ensuring install dir $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

if [[ ! -d "$INSTALL_DIR/.git" ]]; then
  echo "[INFO] Cloning repo..."
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
  git checkout "$BRANCH"
else
  echo "[INFO] Pulling latest changes..."
  cd "$INSTALL_DIR"
  git fetch --all
  git checkout "$BRANCH"
  git pull --ff-only
fi

echo "[INFO] Creating/updating venv..."
$PY_BIN -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
echo "[INFO] Writing systemd service to $SERVICE_FILE"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Tickertronix Hub
After=network.target

[Service]
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/.venv/bin/python3 main_web.py
Restart=always
User=root
EnvironmentFile=-$INSTALL_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

echo "[INFO] Enabling and starting service..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo "[INFO] Avahi (mDNS) should be active. You can test: ping $(hostname).local"
echo "[INFO] Hub should be reachable at http://$(hostname).local:5001/prices (or your LAN IP)."
echo "[INFO] To update later: cd $INSTALL_DIR && git pull && source .venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart $SERVICE_NAME"
