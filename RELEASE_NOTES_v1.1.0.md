# Tickertronix v1.1.0 - Complete System Release

**Release Date**: December 16, 2025
**Release Type**: Minor Update - Documentation & Packaging Improvements

This release focuses on comprehensive documentation enhancements and proper release packaging for all three Tickertronix components.

---

## 📦 What's Included

This release includes binaries/firmware for all three Tickertronix components:

### 🖥️ Raspberry Pi Hub
**File**: `tickertronix-hub-v1.1.0.tar.gz` or `.zip` (86KB / 103KB)
**SHA256**:
- tar.gz: `44b640ba05a2f3a8f5053ee5c9c24fb750dcb7643a2c004a9413f051706dcf89`
- zip: `6919ab1b57de96c591cbc8d5a1cf198e606ba3d5040d3b8029b2ee0fed33ca11`

**Purpose**: Local market data server for your LAN

### 🔲 Matrix Portal Single Firmware
**File**: `matrix-portal-single-v1.1.0.zip` (283KB)
**SHA256**: `8474725867369ecb83d6c38afbbdb494f3452ba05853c462224419a8c3ab4b85`

**Purpose**: Single-asset display firmware for Matrix Portal S3 (64×32 panel)

### 📜 Matrix Portal Scroll Firmware
**File**: `matrix-portal-scroll-v1.1.0.zip` (614KB)
**SHA256**: `e67beca9c169003ec66b38b4bcd97ef1f4d14c3cf588cfcf076ecebe6c5ac4f4`

**Purpose**: Scrolling ticker firmware for Matrix Portal S3 (dual 64×32 panels)

---

## 🎉 What's New in v1.1.0

### Raspberry Pi Hub

#### Added
- **Comprehensive UI Documentation**: Complete guide to Web UI (5 pages) and Desktop GUI (3 screens)
- **Enhanced README**: Detailed descriptions of all interface options and features
- **Device Management Docs**: Documentation for configuring connected display devices
- **Release Automation**: Build scripts for creating distribution packages
- **CHANGELOG.md**: Version history tracking

#### Improved
- Clarified Web UI as default mode for automated setup
- Added port specifications throughout (Web UI: 8080, REST API: 5001)
- Enhanced troubleshooting with separate sections for Web UI and Desktop GUI
- Updated features list with emphasis on dual UI modes

#### Fixed
- Documentation inconsistencies about default UI mode
- Missing UI feature descriptions

### Matrix Portal Firmwares

#### Added
- **Automated Release Packaging**: Firmware build script for consistent releases
- **Installation Guides**: INSTALL.txt included in each firmware package
- **Version Tracking**: VERSION file in firmware packages
- **Complete Package**: All dependencies (fonts/, lib/) included

#### Improved
- Standardized release format for easy installation
- Clear installation instructions for first-time users

---

## 📥 Installation Instructions

### Raspberry Pi Hub

**Quick Start (Automated):**
```bash
# Download and extract
wget https://github.com/Tickertronix/Tickertronix-Open/releases/download/v1.1.0/tickertronix-hub-v1.1.0.tar.gz
tar -xzf tickertronix-hub-v1.1.0.tar.gz
cd tickertronix-hub-v1.1.0

# Run automated setup
sudo ./setup.sh

# Access Web UI
http://tickertronixhub.local:8080
```

**System Requirements:**
- Raspberry Pi (tested on Zero 2 W)
- Raspberry Pi OS Lite (Bookworm, 64-bit)
- Network connection (WiFi or Ethernet)
- Free Alpaca account

### Matrix Portal Single

1. **Prepare Device**: Flash CircuitPython to Matrix Portal S3
2. **Install Firmware**: Unzip and copy all files to CIRCUITPY drive
3. **Provision**: Hold A1 to GND on boot, connect to "TickerSetup" WiFi
4. **Configure**: Enter WiFi credentials and Hub URL at http://192.168.4.1

**Hardware Required:**
- Adafruit Matrix Portal S3
- Single 64×32 RGB LED Matrix Panel
- 5V/2A+ power supply

### Matrix Portal Scroll

1. **Prepare Device**: Flash CircuitPython to Matrix Portal S3
2. **Install Firmware**: Unzip and copy all files/folders to CIRCUITPY drive
3. **Provision**: Hold A1 to GND on boot, connect to "TickerSetup" WiFi
4. **Configure**: Enter WiFi credentials and Hub URL at http://192.168.4.1

**Hardware Required:**
- Adafruit Matrix Portal S3
- Two 64×32 RGB LED Matrix Panels (chained)
- 5V/4A+ power supply

---

## 🔐 Security & Verification

All release packages include SHA256 checksums for verification:

```bash
# Verify Raspberry Pi Hub
sha256sum -c tickertronix-hub-v1.1.0.tar.gz.sha256

# Verify Matrix Portal Single
sha256sum -c matrix-portal-single-v1.1.0.zip.sha256

# Verify Matrix Portal Scroll
sha256sum -c matrix-portal-scroll-v1.1.0.zip.sha256
```

---

## 🌟 Complete Feature Set

### Raspberry Pi Hub Features
- **Dual UI Modes**: Web browser (8080) or desktop GUI (tkinter)
- **Headless Operation**: Perfect for running without a monitor
- **Multi-Asset Tracking**: Stocks, forex, crypto (35 per class)
- **Auto-Updates**: Background scheduler (every 5 minutes)
- **Device Management**: Configure connected Tickertronix displays
- **REST API**: Full HTTP API on port 5001
- **mDNS Discovery**: Access via `tickertronixhub.local`
- **Free Tier**: Uses Alpaca's free market data API

### Matrix Portal Features
- **WiFi Provisioning**: Easy setup via captive portal
- **Local Hub Mode**: No cloud dependencies
- **Configurable Display**: Brightness, speed, dwell time
- **Multi-Asset Support**: Stocks, crypto, forex
- **Visual Indicators**: Color-coded price changes
- **3D Printable Enclosures**: STL files included
- **Low Power**: Efficient CircuitPython firmware

---

## 🐛 Known Issues

None reported for this release.

---

## 📖 Documentation

- **Main README**: [Project Overview](https://github.com/Tickertronix/Tickertronix-Open/blob/main/README.md)
- **Hub Docs**: [Raspberry Pi Hub](https://github.com/Tickertronix/Tickertronix-Open/blob/main/raspberry-pi-hub/README.md)
- **Single Display**: [Matrix Portal Single](https://github.com/Tickertronix/Tickertronix-Open/blob/main/matrix-portal-single/README.md)
- **Scroll Display**: [Matrix Portal Scroll](https://github.com/Tickertronix/Tickertronix-Open/blob/main/matrix-portal-scroll/README.md)
- **CHANGELOG**: [Version History](https://github.com/Tickertronix/Tickertronix-Open/blob/main/CHANGELOG.md)

---

## 🔧 System Architecture

```
┌─────────────────────────────────────────────────┐
│                 Internet                        │
│           (Alpaca Free-Tier API)                │
└──────────────────┬──────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Raspberry Pi Hub  │
         │   (Port 5001)      │◄─── Web UI (Port 8080)
         │  - Fetches prices  │
         │  - Stores locally  │
         │  - Serves API      │
         └─────────┬──────────┘
                   │
         ┌─────────┴─────────┬──────────────┐
         │                   │              │
    ┌────▼─────┐      ┌──────▼────┐   ┌────▼─────┐
    │ Matrix   │      │  Matrix   │   │  Other   │
    │ Portal   │      │  Portal   │   │  Devices │
    │ Single   │      │  Scroll   │   │          │
    └──────────┘      └───────────┘   └──────────┘
```

---

## 🙏 Acknowledgments

Thanks to all contributors and users providing feedback!

Special thanks to:
- Adafruit for the Matrix Portal S3 platform
- Alpaca for free-tier market data access
- CircuitPython community

---

## 🔗 Links

- **GitHub**: https://github.com/Tickertronix/Tickertronix-Open
- **Issues**: https://github.com/Tickertronix/Tickertronix-Open/issues
- **Discussions**: https://github.com/Tickertronix/Tickertronix-Open/discussions
- **Full Changelog**: https://github.com/Tickertronix/Tickertronix-Open/compare/v1.0.1...v1.1.0

---

## ⚠️ Important Notes

1. **Hub Required**: Matrix Portal devices require a Tickertronix Hub to function
2. **Network**: All components must be on the same local network
3. **Power**: Ensure adequate power supply for LED matrices (2A minimum per panel)
4. **API Keys**: Free Alpaca account required for market data

---

**Enjoy your Tickertronix system!** 🚀

For support, please open an issue on GitHub.
