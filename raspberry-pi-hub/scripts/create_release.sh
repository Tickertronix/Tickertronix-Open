#!/bin/bash
#===============================================================================
# Tickertronix Hub - Release Builder
#===============================================================================
# Creates release archives for distribution
#
# Usage:
#   ./scripts/create_release.sh VERSION
#   Example: ./scripts/create_release.sh 1.1.0
#===============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Error: Version number required${NC}"
    echo "Usage: $0 VERSION"
    echo "Example: $0 1.1.0"
    exit 1
fi

VERSION="$1"
RELEASE_NAME="tickertronix-hub-v${VERSION}"

# Use root-level releases directory with version subdirectory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_DIR="$(dirname "${SCRIPT_DIR}")"
PROJECT_ROOT="$(dirname "${HUB_DIR}")"
RELEASE_DIR="${PROJECT_ROOT}/releases/v${VERSION}"
BUILD_DIR="${RELEASE_DIR}/${RELEASE_NAME}"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Tickertronix Hub - Release Builder v${VERSION}         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Create release directory
echo -e "${GREEN}[1/6]${NC} Creating release directory..."
mkdir -p "${BUILD_DIR}"

# Copy project files
echo -e "${GREEN}[2/6]${NC} Copying project files..."
cd "${HUB_DIR}"
cp -r \
    *.py \
    requirements.txt \
    README.md \
    config.py \
    setup.sh \
    "${BUILD_DIR}/" 2>/dev/null || true

# Copy LICENSE from project root if exists
if [ -f "${PROJECT_ROOT}/LICENSE" ]; then
    cp "${PROJECT_ROOT}/LICENSE" "${BUILD_DIR}/"
fi

# Copy scripts directory (excluding this build script)
echo -e "${GREEN}[3/6]${NC} Copying scripts..."
mkdir -p "${BUILD_DIR}/scripts"
cp scripts/*.py "${BUILD_DIR}/scripts/" 2>/dev/null || true
cp scripts/setup_pi.sh "${BUILD_DIR}/scripts/" 2>/dev/null || true
cp scripts/cleanup_price_history.py "${BUILD_DIR}/scripts/" 2>/dev/null || true

# Copy templates and static files if they exist
echo -e "${GREEN}[4/6]${NC} Copying web assets..."
if [ -d "templates" ]; then
    cp -r templates "${BUILD_DIR}/"
fi
if [ -d "static" ]; then
    cp -r static "${BUILD_DIR}/"
fi

# Copy documentation
if [ -d "docs" ]; then
    cp -r docs "${BUILD_DIR}/"
fi

# Create version file
echo -e "${GREEN}[5/6]${NC} Creating version file..."
echo "${VERSION}" > "${BUILD_DIR}/VERSION"
cat > "${BUILD_DIR}/RELEASE_INFO.txt" << EOF
Tickertronix Hub - Release v${VERSION}
======================================

Build Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Git Commit: $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

Installation:
-------------
1. Extract this archive to your Raspberry Pi
2. Run: sudo ./setup.sh
3. Configure credentials: tickertronix setup-credentials
4. Access Web UI: http://tickertronixhub.local:8080

For full documentation, see README.md

Project: https://github.com/Tickertronix/Tickertronix-Open
EOF

# Create archives
echo -e "${GREEN}[6/6]${NC} Creating release archives..."
cd "${RELEASE_DIR}"

# Create tar.gz
tar -czf "${RELEASE_NAME}.tar.gz" "${RELEASE_NAME}/"
echo -e "  ✓ Created ${RELEASE_NAME}.tar.gz"

# Create zip
zip -r -q "${RELEASE_NAME}.zip" "${RELEASE_NAME}/"
echo -e "  ✓ Created ${RELEASE_NAME}.zip"

cd ..

# Calculate checksums
echo ""
echo -e "${GREEN}Generating checksums...${NC}"
cd "${RELEASE_DIR}"
sha256sum "${RELEASE_NAME}.tar.gz" > "${RELEASE_NAME}.tar.gz.sha256"
sha256sum "${RELEASE_NAME}.zip" > "${RELEASE_NAME}.zip.sha256"
cd ..

# Summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Release Complete!                         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Release artifacts:${NC}"
echo "  📦 ${RELEASE_DIR}/${RELEASE_NAME}.tar.gz"
echo "  📦 ${RELEASE_DIR}/${RELEASE_NAME}.zip"
echo "  🔐 ${RELEASE_DIR}/${RELEASE_NAME}.tar.gz.sha256"
echo "  🔐 ${RELEASE_DIR}/${RELEASE_NAME}.zip.sha256"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Create git tag: git tag -a v${VERSION} -m 'Release v${VERSION}'"
echo "  2. Push tag: git push origin v${VERSION}"
echo "  3. Create GitHub release with all firmware packages"
echo ""
echo "  From project root:"
echo "  cd ${PROJECT_ROOT}"
echo "  gh release create v${VERSION} releases/*-v${VERSION}.* --title 'v${VERSION}' --notes-file RELEASE_NOTES_v${VERSION}.md"
echo ""
