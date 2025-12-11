#!/bin/bash -e

TICKERTRONIX_REPO_URL=${TICKERTRONIX_REPO_URL:-https://github.com/Tickertronix/Tickertronix-Open.git}
TICKERTRONIX_REF=${TICKERTRONIX_REF:-main}
TICKERTRONIX_SUBDIR=${TICKERTRONIX_SUBDIR:-raspberry-pi-hub}
TICKERTRONIX_INSTALL_DIR=${TICKERTRONIX_INSTALL_DIR:-/opt/tickertronix}
TICKERTRONIX_SERVICE_NAME=${TICKERTRONIX_SERVICE_NAME:-tickertronixhub}
TICKERTRONIX_SERVICE_USER=${TICKERTRONIX_SERVICE_USER:-pi}

INSTALL_PATH="${ROOTFS_DIR}${TICKERTRONIX_INSTALL_DIR}"
rm -rf "${INSTALL_PATH}"
install -d "${INSTALL_PATH}"

# Clone the full repo to a temp directory
TEMP_CLONE=$(mktemp -d)
trap "rm -rf ${TEMP_CLONE}" EXIT
GIT_TERMINAL_PROMPT=0 git clone --depth 1 --branch "${TICKERTRONIX_REF}" "${TICKERTRONIX_REPO_URL}" "${TEMP_CLONE}"

# Copy the raspberry-pi-hub subdirectory to the install location
cp -r "${TEMP_CLONE}/${TICKERTRONIX_SUBDIR}/." "${INSTALL_PATH}/"

on_chroot <<EOF
set -euo pipefail

REPO_URL="${TICKERTRONIX_REPO_URL}"
REPO_REF="${TICKERTRONIX_REF}"
INSTALL_DIR="${TICKERTRONIX_INSTALL_DIR}"
SERVICE_NAME="${TICKERTRONIX_SERVICE_NAME}"
SERVICE_USER="${TICKERTRONIX_SERVICE_USER}"

id -u "\$SERVICE_USER" >/dev/null 2>&1 || useradd -m "\$SERVICE_USER"

cd "\$INSTALL_DIR"

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
