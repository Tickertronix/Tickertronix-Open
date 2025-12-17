# Tickertronix Hub v1.1.0 - Enhanced UI Documentation

This release focuses on comprehensive documentation improvements, making the dual UI modes (Web UI and Desktop GUI) crystal clear for users.

## 🎉 What's New

### 📚 Comprehensive UI Documentation
- **Complete Web UI Guide**: Detailed documentation of all 5 web pages (Dashboard, Credentials, Assets, Prices, Devices)
- **Tkinter GUI Documentation**: Full description of all desktop GUI screens and features
- **Clear Mode Comparison**: Web UI (headless/remote) vs Desktop GUI (local display)

### 🔧 Improvements
- Enhanced README with explicit UI mode descriptions
- Clarified that automated setup (`setup.sh`) uses Web UI mode by default
- Added port specifications throughout (Web UI: 8080, REST API: 5001)
- Improved troubleshooting section with separate Web UI and GUI guidance

### 📦 Release Automation
- New release build script for creating distribution packages
- Automated checksum generation for security verification
- CHANGELOG.md for tracking version history

## 📥 Installation

### Quick Start (Recommended)
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

### Manual Installation
See the [README.md](https://github.com/Tickertronix/Tickertronix-Open/blob/main/raspberry-pi-hub/README.md) for detailed manual installation instructions.

## 🔐 Checksums

**SHA256**:
- `tickertronix-hub-v1.1.0.tar.gz`: `44b640ba05a2f3a8f5053ee5c9c24fb750dcb7643a2c004a9413f051706dcf89`
- `tickertronix-hub-v1.1.0.zip`: `6919ab1b57de96c591cbc8d5a1cf198e606ba3d5040d3b8029b2ee0fed33ca11`

Verify with:
```bash
sha256sum -c tickertronix-hub-v1.1.0.tar.gz.sha256
```

## 📋 System Requirements

- **Hardware**: Raspberry Pi (tested on Zero 2 W)
- **OS**: Raspberry Pi OS Lite (Bookworm, 64-bit recommended)
- **Network**: WiFi or Ethernet connection
- **API**: Free Alpaca account (https://alpaca.markets)

## 🌟 Features

- **Dual UI Modes**: Web browser interface (8080) or desktop GUI (tkinter)
- **Headless Operation**: Perfect for running without a monitor
- **Multi-Asset Tracking**: Stocks, forex, and crypto (35 per class)
- **Auto-Updates**: Background scheduler (every 5 minutes)
- **Device Management**: Configure connected Tickertronix displays
- **Local API**: REST endpoints on port 5001
- **mDNS Discovery**: Access via `tickertronixhub.local`

## 🐛 Bug Fixes

- Fixed documentation inconsistencies about default UI mode
- Clarified Web UI as the recommended approach for headless setups

## 📖 Documentation

- [README](https://github.com/Tickertronix/Tickertronix-Open/blob/main/raspberry-pi-hub/README.md)
- [CHANGELOG](https://github.com/Tickertronix/Tickertronix-Open/blob/main/raspberry-pi-hub/CHANGELOG.md)
- [Project Home](https://github.com/Tickertronix/Tickertronix-Open)

## ⚠️ Known Issues

None reported for this release.

## 🙏 Acknowledgments

Thanks to all contributors and users providing feedback!

---

**Full Changelog**: https://github.com/Tickertronix/Tickertronix-Open/compare/v1.0.1...v1.1.0
