#!/usr/bin/env bash
# Build drag-and-drop release ZIPs for Matrix Portal devices.
#
# Usage:
#   ./scripts/build_matrix_portal_releases.sh
#
# Outputs:
#   dist/matrix-portal-scroll.zip   # Scroll ticker bundle (with libs/fonts)
#   dist/matrix-portal-single.zip   # Single-asset bundle (with libs/fonts)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"

mkdir -p "${DIST_DIR}"

build_scroll() {
  local stage="${DIST_DIR}/matrix-portal-scroll"
  rm -rf "${stage}"
  mkdir -p "${stage}"

  cp "${ROOT_DIR}/matrix-portal-scroll"/{code.py,api_client.py,provisioning_v2.py,wifimgr.py,boot.py,boot_logo.py,time_sync.py,neopixel.mpy,settings.toml,device_config.json.sample} "${stage}/"
  cp -R "${ROOT_DIR}/matrix-portal-scroll/fonts" "${stage}/"
  cp -R "${ROOT_DIR}/matrix-portal-scroll/lib" "${stage}/"

  # Clean unwanted artifacts
  find "${stage}" -name "__pycache__" -prune -exec rm -rf {} +
  find "${stage}" -name ".DS_Store" -delete

  (cd "${stage}" && zip -r "${DIST_DIR}/matrix-portal-scroll.zip" .)
  echo "Built ${DIST_DIR}/matrix-portal-scroll.zip"
}

build_single() {
  local stage="${DIST_DIR}/matrix-portal-single"
  rm -rf "${stage}"
  mkdir -p "${stage}"

  cp "${ROOT_DIR}/matrix-portal-single"/{code.py,api_client.py,provisioning_v2.py,wifimgr.py,boot.py,time_sync.py} "${stage}/"
  cp -R "${ROOT_DIR}/matrix-portal-single/fonts" "${stage}/"

  # Reuse the scroll build's tested library bundle
  cp -R "${ROOT_DIR}/matrix-portal-scroll/lib" "${stage}/"

  find "${stage}" -name "__pycache__" -prune -exec rm -rf {} +
  find "${stage}" -name ".DS_Store" -delete

  (cd "${stage}" && zip -r "${DIST_DIR}/matrix-portal-single.zip" .)
  echo "Built ${DIST_DIR}/matrix-portal-single.zip"
}

build_scroll
build_single

echo "Done. Drag-and-drop bundles are in ${DIST_DIR}/"
