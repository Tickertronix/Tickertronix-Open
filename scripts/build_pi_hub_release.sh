#!/usr/bin/env bash
# Build Raspberry Pi Hub release tarball
#
# Usage:
#   ./scripts/build_pi_hub_release.sh VERSION
#
# Example:
#   ./scripts/build_pi_hub_release.sh 1.1.0
#
# Output:
#   dist/tickertronix-raspberry-pi-hub-v{VERSION}.tar.gz

set -euo pipefail

VERSION="${1:-dev}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"

mkdir -p "${DIST_DIR}"

OUTPUT="tickertronix-raspberry-pi-hub-v${VERSION}.tar.gz"

echo "Building Pi Hub release bundle (version: ${VERSION})..."

cd "${ROOT_DIR}"
tar -czf "${DIST_DIR}/${OUTPUT}" \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.gitignore' \
  --exclude='data' \
  --exclude='logs' \
  --exclude='venv' \
  --exclude='.venv' \
  --exclude='test_*.py' \
  --exclude='debug_*.py' \
  raspberry-pi-hub/

echo "Built ${DIST_DIR}/${OUTPUT}"
