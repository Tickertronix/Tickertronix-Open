#!/bin/bash -e

TICKERTRONIX_REPO_URL=${TICKERTRONIX_REPO_URL:-https://github.com/tickertronix/alpaca-price-hub.git}
TICKERTRONIX_REF=${TICKERTRONIX_REF:-main}
TICKERTRONIX_INSTALL_DIR=${TICKERTRONIX_INSTALL_DIR:-/opt/tickertronix}
TICKERTRONIX_SERVICE_NAME=${TICKERTRONIX_SERVICE_NAME:-tickertronixhub}
TICKERTRONIX_SERVICE_USER=${TICKERTRONIX_SERVICE_USER:-pi}

install -d "${ROOTFS_DIR}${TICKERTRONIX_INSTALL_DIR}"

on_chroot <<EOF
set -euo pipefail

REPO_URL="${TICKERTRONIX_REPO_URL}"
REPO_REF="${TICKERTRONIX_REF}"
INSTALL_DIR="${TICKERTRONIX_INSTALL_DIR}"
SERVICE_NAME="${TICKERTRONIX_SERVICE_NAME}"
SERVICE_USER="${TICKERTRONIX_SERVICE_USER}"

id -u "\$SERVICE_USER" >/dev/null 2>&1 || useradd -m "\$SERVICE_USER"

rm -rf "\$INSTALL_DIR"
git clone "\$REPO_URL" "\$INSTALL_DIR"
cd "\$INSTALL_DIR"
git checkout "\$REPO_REF"

python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
rm -rf /root/.cache/pip
chown -R "\$SERVICE_USER":"\$SERVICE_USER" "\$INSTALL_DIR"

cat >/etc/systemd/system/\${SERVICE_NAME}.service <<SERVICE
[Unit]
Description=Tickertronix Hub (Market data + web UI)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=\${SERVICE_USER}
WorkingDirectory=\${INSTALL_DIR}
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=-\${INSTALL_DIR}/.env
ExecStart=\${INSTALL_DIR}/.venv/bin/python3 main_web.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable "\${SERVICE_NAME}.service"
systemctl enable avahi-daemon.service
EOF
