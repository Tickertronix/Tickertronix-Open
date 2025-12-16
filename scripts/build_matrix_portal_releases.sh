#!/usr/bin/env bash
# Build drag-and-drop release ZIPs for Matrix Portal devices.
#
# Usage:
#   ./scripts/build_matrix_portal_releases.sh [VERSION]
#
# Examples:
#   ./scripts/build_matrix_portal_releases.sh 1.1.0
#   ./scripts/build_matrix_portal_releases.sh        # defaults to unversioned
#
# Outputs:
#   dist/tickertronix-matrix-portal-scroll-v{VERSION}.zip
#   dist/tickertronix-matrix-portal-single-v{VERSION}.zip

set -euo pipefail

VERSION="${1:-}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"

mkdir -p "${DIST_DIR}"

# Version suffix for filenames
if [ -n "$VERSION" ]; then
  SUFFIX="-v${VERSION}"
else
  SUFFIX=""
fi

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

  (cd "${stage}" && zip -r "${DIST_DIR}/tickertronix-matrix-portal-scroll${SUFFIX}.zip" .)
  echo "Built ${DIST_DIR}/tickertronix-matrix-portal-scroll${SUFFIX}.zip"
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

  (cd "${stage}" && zip -r "${DIST_DIR}/tickertronix-matrix-portal-single${SUFFIX}.zip" .)
  echo "Built ${DIST_DIR}/tickertronix-matrix-portal-single${SUFFIX}.zip"
}

build_scroll
build_single

echo "Done. Drag-and-drop bundles are in ${DIST_DIR}/"
