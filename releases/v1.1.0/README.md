# Tickertronix v1.1.0 - Release Package

**Release Date**: December 16, 2025

This directory contains all release binaries for Tickertronix v1.1.0.

---

## 📦 Contents

### Raspberry Pi Hub (Python/Flask)
Market data server for your local network.

**Archives:**
- `tickertronix-hub-v1.1.0.tar.gz` (86KB) - Linux/Unix format
- `tickertronix-hub-v1.1.0.zip` (103KB) - Universal format

**Checksums:**
- `tickertronix-hub-v1.1.0.tar.gz.sha256`
- `tickertronix-hub-v1.1.0.zip.sha256`

**Installation:**
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

---

### Matrix Portal Single Firmware (CircuitPython)
Single-panel display showing one asset at a time.

**Archive:**
- `matrix-portal-single-v1.1.0.zip` (283KB)

**Checksum:**
- `matrix-portal-single-v1.1.0.zip.sha256`

**Installation:**
1. Flash CircuitPython to Matrix Portal S3
2. Unzip and copy all files to CIRCUITPY drive
3. Hold A1 to GND on boot for provisioning
4. Connect to "TickerSetup" WiFi, configure at http://192.168.4.1

**Hardware Required:**
- Adafruit Matrix Portal S3
- Single 64×32 RGB LED Matrix Panel
- 5V/2A+ power supply

---

### Matrix Portal Scroll Firmware (CircuitPython)
Dual-panel scrolling ticker display.

**Archive:**
- `matrix-portal-scroll-v1.1.0.zip` (614KB)

**Checksum:**
- `matrix-portal-scroll-v1.1.0.zip.sha256`

**Installation:**
1. Flash CircuitPython to Matrix Portal S3
2. Unzip and copy all files/folders to CIRCUITPY drive (preserve lib/ and fonts/)
3. Hold A1 to GND on boot for provisioning
4. Connect to "TickerSetup" WiFi, configure at http://192.168.4.1

**Hardware Required:**
- Adafruit Matrix Portal S3
- Two 64×32 RGB LED Matrix Panels (chained)
- 5V/4A+ power supply

---

## 🔐 Verification

All packages include SHA256 checksums for integrity verification:

```bash
# Verify any package
sha256sum -c <filename>.sha256
```

**Full Checksums:**
```
44b640ba05a2f3a8f5053ee5c9c24fb750dcb7643a2c004a9413f051706dcf89  tickertronix-hub-v1.1.0.tar.gz
6919ab1b57de96c591cbc8d5a1cf198e606ba3d5040d3b8029b2ee0fed33ca11  tickertronix-hub-v1.1.0.zip
8474725867369ecb83d6c38afbbdb494f3452ba05853c462224419a8c3ab4b85  matrix-portal-single-v1.1.0.zip
e67beca9c169003ec66b38b4bcd97ef1f4d14c3cf588cfcf076ecebe6c5ac4f4  matrix-portal-scroll-v1.1.0.zip
```

---

## 📊 Package Summary

| Component | Archive | Size | Type |
|-----------|---------|------|------|
| **Pi Hub** | .tar.gz | 86KB | Python/Flask |
| **Pi Hub** | .zip | 103KB | Python/Flask |
| **Single** | .zip | 283KB | CircuitPython |
| **Scroll** | .zip | 614KB | CircuitPython |
| **Total** | - | ~1.1 MB | - |

---

## 🌟 What's New in v1.1.0

### Raspberry Pi Hub
- Comprehensive UI documentation (Web UI + Desktop GUI)
- Enhanced README with detailed feature descriptions
- Device management documentation
- Release automation scripts
- CHANGELOG for version tracking

### Matrix Portal Firmwares
- Automated release packaging
- Installation guides included in packages
- Complete dependency bundles (fonts/, lib/)
- Version tracking in releases

---

## 📖 Documentation

- [Main Project README](https://github.com/Tickertronix/Tickertronix-Open/blob/main/README.md)
- [Raspberry Pi Hub Guide](https://github.com/Tickertronix/Tickertronix-Open/blob/main/raspberry-pi-hub/README.md)
- [Matrix Portal Single Guide](https://github.com/Tickertronix/Tickertronix-Open/blob/main/matrix-portal-single/README.md)
- [Matrix Portal Scroll Guide](https://github.com/Tickertronix/Tickertronix-Open/blob/main/matrix-portal-scroll/README.md)
- [Full Changelog](https://github.com/Tickertronix/Tickertronix-Open/blob/main/CHANGELOG.md)

---

## 🆘 Support

- **Issues**: https://github.com/Tickertronix/Tickertronix-Open/issues
- **Discussions**: https://github.com/Tickertronix/Tickertronix-Open/discussions

---

**Enjoy your Tickertronix system!** 🚀
