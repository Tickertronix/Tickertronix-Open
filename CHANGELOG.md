# Changelog

All notable changes to Tickertronix-Open will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2025-12-16

### Added
- Coming soon...

## [1.1.0] - 2025-12-16

### Added - Raspberry Pi Hub
- **Comprehensive UI Documentation**: Detailed description of Web UI (5 pages) and Desktop GUI (3 screens)
- **Enhanced README**: Complete guide to all interface features and modes
- **Device Management Documentation**: Full docs for configuring connected displays
- **Release Automation**: `scripts/create_release.sh` for building distribution packages
- **CHANGELOG.md**: Version history tracking in hub directory
- **Release Notes**: Detailed release announcement templates

### Added - Matrix Portal Firmwares
- **Firmware Build Script**: `scripts/create_firmware_releases.sh` for automated packaging
- **Installation Guides**: INSTALL.txt files included in each firmware package
- **Version Tracking**: VERSION file in all firmware releases
- **Complete Packages**: All dependencies (fonts/, lib/) included in releases

### Changed - Raspberry Pi Hub
- **README Improvements**: Extensive UI documentation with page-by-page breakdown
- **Quick Start Guide**: Clarified that automated setup uses Web UI by default
- **Features List**: Updated to emphasize dual UI modes and port specifications
- **Troubleshooting**: Separate sections for Web UI and Desktop GUI issues
- **Usage Section**: Split into Web UI Mode and Desktop GUI Mode with clear examples

### Changed - Release Process
- **Automated Builds**: Scripts now create consistent, versioned release packages
- **Checksums**: SHA256 checksums generated for all release artifacts
- **Documentation**: Unified release notes covering all three components

### Fixed
- **Documentation Accuracy**: Corrected default UI mode references (Web UI, not tkinter)
- **Missing UI Details**: README now properly describes available interfaces
- **Setup Clarity**: Clarified that `setup.sh` uses `main_web.py` by default

### Documentation
- Added comprehensive Web UI feature descriptions (Dashboard, Credentials, Assets, Prices, Devices)
- Documented all tkinter GUI screens (Credentials, Asset Selection, Status & Prices)
- Included port information throughout (Web UI: 8080, REST API: 5001)
- Added mDNS access instructions and troubleshooting
- Created unified release documentation for entire system

## [1.0.1] - 2025-12-12

### Added
- GitHub Actions for automated releases on version tags
- Community health files:
  - CODE_OF_CONDUCT.md (Contributor Covenant v2.1)
  - SECURITY.md (vulnerability reporting policy)
- Issue templates (bug report, feature request forms)
- Pull request template with testing checklist
- Versioned release asset naming (`tickertronix-{device}-v{version}.zip`)
- Build scripts for Pi Hub tarball and CYD source bundle

### Changed
- Build scripts now accept version parameter for automated builds
- README "Release Bundles" section updated with versioned asset names
- Release process fully automated via GitHub Actions

## [1.0.0] - 2025-12-11

### Added
- Initial public release
- Raspberry Pi Hub with REST API for market data
- Matrix Portal Scroll display support (1-6 panels)
- Matrix Portal Single display support (single panel with paging)
- CYD Ticker (ESP32-2432S028R) display support
- HMAC authentication for secure device communication
- Local hub mode for LAN-only operation
- WiFi provisioning via captive portal for embedded devices
- 3D printable enclosures for all display types
- Comprehensive documentation for all components
- Support for stocks, crypto, and forex via Alpaca and Twelve Data APIs

### Changed
- Standardized default credentials across documentation (username: tickertronix)
- Updated to use Alpaca free-tier API
- Improved provisioning workflow for display devices
- Enhanced security with credential storage in SQLite

### Security
- No hardcoded credentials in source code
- SQLite database for secure API key storage
- Environment variable support for systemd services
- Default credentials documented with security warnings
- Removed pi-gen directory from version control

### Documentation
- Created comprehensive root README for project overview
- Added complete CYD component documentation
- Enhanced Matrix Portal Single documentation
- Added CONTRIBUTING.md and this CHANGELOG
- Standardized credential references (tickertronix@tickertronixhub.local)
