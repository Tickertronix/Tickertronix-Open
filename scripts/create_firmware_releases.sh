#!/bin/bash
#===============================================================================
# Tickertronix Firmware - Release Builder
#===============================================================================
# Creates release archives for Matrix Portal firmwares
#
# Usage:
#   ./scripts/create_firmware_releases.sh VERSION
#   Example: ./scripts/create_firmware_releases.sh 1.1.0
#===============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Error: Version number required${NC}"
    echo "Usage: $0 VERSION"
    echo "Example: $0 1.1.0"
    exit 1
fi

VERSION="$1"

# Determine project root (script is in scripts/ subdirectory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
RELEASE_DIR="${PROJECT_ROOT}/releases/v${VERSION}"

cd "${PROJECT_ROOT}"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Tickertronix Firmware - Release Builder v${VERSION}       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Create release directory
mkdir -p "${RELEASE_DIR}"

#===============================================================================
# Build Matrix Portal Single Release
#===============================================================================

echo -e "${YELLOW}Building Matrix Portal Single Firmware...${NC}"
SINGLE_NAME="matrix-portal-single-v${VERSION}"
SINGLE_DIR="${RELEASE_DIR}/${SINGLE_NAME}"

echo -e "${GREEN}[1/3]${NC} Creating directory structure..."
mkdir -p "${SINGLE_DIR}"

echo -e "${GREEN}[2/3]${NC} Copying firmware files..."
cd matrix-portal-single

# Copy main firmware files
cp code.py api_client.py provisioning_v2.py wifimgr.py boot.py time_sync.py boot_logo.py "${SINGLE_DIR}/"

# Copy boot logo if exists
if [ -f "boot_logo.bmp" ]; then
    cp boot_logo.bmp "${SINGLE_DIR}/"
fi

# Copy fonts directory
if [ -d "fonts" ]; then
    cp -r fonts "${SINGLE_DIR}/"
fi

# Copy 3D files
if [ -d "3D Files" ]; then
    cp -r "3D Files" "${SINGLE_DIR}/"
fi

# Copy documentation
cp README.md "${SINGLE_DIR}/"

# Create installation guide
cat > "${SINGLE_DIR}/INSTALL.txt" << 'EOF'
Tickertronix Matrix Portal Single - Installation Instructions
==============================================================

1. PREPARE YOUR DEVICE
   - Connect Matrix Portal S3 via USB-C
   - Double-tap RESET button to enter bootloader mode
   - Device will appear as "RPI-RP2" USB drive

2. INSTALL CIRCUITPYTHON
   - Download CircuitPython for Matrix Portal S3:
     https://circuitpython.org/board/matrixportal_s3/
   - Drag the .UF2 file to the RPI-RP2 drive
   - Device will reboot and appear as "CIRCUITPY"

3. INSTALL FIRMWARE
   - Copy ALL files from this release to CIRCUITPY drive
   - Maintain directory structure (keep fonts/ folder intact)
   - Device will automatically reboot

4. FIRST-TIME SETUP
   - Hold A1 button to GND on boot to enter provisioning
   - Connect to WiFi network "TickerSetup"
   - Open browser to http://192.168.4.1
   - Enter your WiFi credentials and Hub URL
   - Example Hub URL: http://192.168.1.100:5001

5. NORMAL OPERATION
   - Device will automatically connect to WiFi
   - Fetches price data from your Tickertronix Hub
   - Cycles through assets with configurable dwell time

For detailed documentation, see README.md

Troubleshooting: https://github.com/Tickertronix/Tickertronix-Open/issues
EOF

# Create version file
echo "${VERSION}" > "${SINGLE_DIR}/VERSION"

cd "${PROJECT_ROOT}"

echo -e "${GREEN}[3/3]${NC} Creating archive..."
cd "${RELEASE_DIR}"
zip -r -q "${SINGLE_NAME}.zip" "${SINGLE_NAME}/"
echo -e "  ✓ Created ${SINGLE_NAME}.zip"
cd "${PROJECT_ROOT}"

#===============================================================================
# Build Matrix Portal Scroll Release
#===============================================================================

echo ""
echo -e "${YELLOW}Building Matrix Portal Scroll Firmware...${NC}"
SCROLL_NAME="matrix-portal-scroll-v${VERSION}"
SCROLL_DIR="${RELEASE_DIR}/${SCROLL_NAME}"

echo -e "${GREEN}[1/3]${NC} Creating directory structure..."
mkdir -p "${SCROLL_DIR}"

echo -e "${GREEN}[2/3]${NC} Copying firmware files..."
cd matrix-portal-scroll

# Copy main firmware files
cp code.py api_client.py provisioning_v2.py wifimgr.py boot.py time_sync.py boot_logo.py "${SCROLL_DIR}/"

# Copy boot logo if exists
if [ -f "boot_logo.bmp" ]; then
    cp boot_logo.bmp "${SCROLL_DIR}/"
fi

# Copy neopixel if exists
if [ -f "neopixel.mpy" ]; then
    cp neopixel.mpy "${SCROLL_DIR}/"
fi

# Copy fonts directory
if [ -d "fonts" ]; then
    cp -r fonts "${SCROLL_DIR}/"
fi

# Copy lib directory
if [ -d "lib" ]; then
    cp -r lib "${SCROLL_DIR}/"
fi

# Copy 3D files
if [ -d "3D Files" ]; then
    cp -r "3D Files" "${SCROLL_DIR}/"
fi

# Copy documentation
cp README.md "${SCROLL_DIR}/"
if [ -f "SETUP_INSTRUCTIONS.md" ]; then
    cp SETUP_INSTRUCTIONS.md "${SCROLL_DIR}/"
fi

# Copy device config sample
if [ -f "device_config.json.sample" ]; then
    cp device_config.json.sample "${SCROLL_DIR}/"
fi

# Create installation guide
cat > "${SCROLL_DIR}/INSTALL.txt" << 'EOF'
Tickertronix Matrix Portal Scroll - Installation Instructions
==============================================================

1. PREPARE YOUR DEVICE
   - Connect Matrix Portal S3 via USB-C
   - Double-tap RESET button to enter bootloader mode
   - Device will appear as "RPI-RP2" USB drive

2. INSTALL CIRCUITPYTHON
   - Download CircuitPython for Matrix Portal S3:
     https://circuitpython.org/board/matrixportal_s3/
   - Drag the .UF2 file to the RPI-RP2 drive
   - Device will reboot and appear as "CIRCUITPY"

3. INSTALL FIRMWARE
   - Copy ALL files and folders from this release to CIRCUITPY drive
   - IMPORTANT: Keep folder structure intact (lib/, fonts/)
   - Device will automatically reboot

4. FIRST-TIME SETUP
   - Hold A1 button to GND on boot to enter provisioning
   - Connect to WiFi network "TickerSetup"
   - Open browser to http://192.168.4.1
   - Enter your WiFi credentials and Hub URL
   - Example Hub URL: http://192.168.1.100:5001

5. NORMAL OPERATION
   - Device will automatically connect to WiFi
   - Fetches price data from your Tickertronix Hub
   - Scrolls through stocks, crypto, and forex continuously

Configuration:
- Copy device_config.json.sample to device_config.json for custom settings
- Adjust scroll speed, brightness, and display preferences

For detailed documentation, see README.md

Troubleshooting: https://github.com/Tickertronix/Tickertronix-Open/issues
EOF

# Create version file
echo "${VERSION}" > "${SCROLL_DIR}/VERSION"

cd "${PROJECT_ROOT}"

echo -e "${GREEN}[3/3]${NC} Creating archive..."
cd "${RELEASE_DIR}"
zip -r -q "${SCROLL_NAME}.zip" "${SCROLL_NAME}/"
echo -e "  ✓ Created ${SCROLL_NAME}.zip"
cd "${PROJECT_ROOT}"

#===============================================================================
# Generate Checksums
#===============================================================================

echo ""
echo -e "${GREEN}Generating checksums...${NC}"
cd "${RELEASE_DIR}"
sha256sum "${SINGLE_NAME}.zip" > "${SINGLE_NAME}.zip.sha256"
sha256sum "${SCROLL_NAME}.zip" > "${SCROLL_NAME}.zip.sha256"
cd "${PROJECT_ROOT}"

#===============================================================================
# Summary
#===============================================================================

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Firmware Releases Complete!                     ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Release artifacts:${NC}"
echo "  📦 ${RELEASE_DIR}/${SINGLE_NAME}.zip"
echo "  🔐 ${RELEASE_DIR}/${SINGLE_NAME}.zip.sha256"
echo "  📦 ${RELEASE_DIR}/${SCROLL_NAME}.zip"
echo "  🔐 ${RELEASE_DIR}/${SCROLL_NAME}.zip.sha256"
echo ""
echo -e "${GREEN}File sizes:${NC}"
du -h "${RELEASE_DIR}/${SINGLE_NAME}.zip" | awk '{print "  " $1 " - Matrix Portal Single"}'
du -h "${RELEASE_DIR}/${SCROLL_NAME}.zip" | awk '{print "  " $1 " - Matrix Portal Scroll"}'
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Create git tag: git tag -a v${VERSION} -m 'Release v${VERSION}'"
echo "  2. Push tag: git push origin v${VERSION}"
echo "  3. Create GitHub release with all firmware packages"
echo ""
echo "  Or use: gh release create v${VERSION} ${RELEASE_DIR}/*-v${VERSION}.* --title 'v${VERSION}'"
echo ""
