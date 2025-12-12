#!/usr/bin/env bash
# Build CYD Ticker source bundle
#
# Usage:
#   ./scripts/build_cyd_source_release.sh VERSION
#
# Example:
#   ./scripts/build_cyd_source_release.sh 1.0.0
#
# Output:
#   dist/tickertronix-cyd-ticker-source-v{VERSION}.zip

set -euo pipefail

VERSION="${1:-dev}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"

mkdir -p "${DIST_DIR}"

OUTPUT="tickertronix-cyd-ticker-source-v${VERSION}.zip"

echo "Building CYD source bundle (version: ${VERSION})..."

cd "${ROOT_DIR}"
zip -r "${DIST_DIR}/${OUTPUT}" \
  cyd-ticker-il9341/ \
  -x "*.pyc" "*__pycache__*" "*/.gitignore" "*/build/*" "*/.DS_Store" "*/.claude/*"

echo "Built ${DIST_DIR}/${OUTPUT}"
