# Changelog

All notable changes to Tickertronix Hub will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-12-16

### Added
- Comprehensive UI documentation in README
  - Detailed Web UI section with all 5 pages described (Dashboard, Credentials, Assets, Prices, Devices)
  - Complete Tkinter GUI documentation with all interface tabs
  - Clear comparison between headless (Web UI) and desktop (GUI) modes
- Enhanced README features section highlighting dual UI modes
- Device management capabilities documentation
- Web UI troubleshooting section in README
- Release build automation script (`scripts/create_release.sh`)
- This CHANGELOG file to track version history

### Changed
- Updated README.md with extensive UI/UX documentation
- Improved "Quick Start" section with clearer Web UI access instructions
- Enhanced "Usage" section split into Web UI and Desktop GUI modes
- Reorganized troubleshooting section with separate Web UI and GUI sections
- Updated features list to emphasize dual UI modes and port specifications

### Fixed
- README now accurately describes the Web UI as the default mode for automated setup
- Clarified that `setup.sh` uses `main_web.py` by default, not `main.py`

### Documentation
- Added detailed page-by-page breakdown of Web UI functionality
- Documented all tkinter GUI screens and their features
- Added port information (8080 for Web UI, 5001 for REST API)
- Included mDNS access instructions for LAN devices

## [1.0.1] - Previous Release

### Added
- Initial stable release
- Alpaca API integration for market data
- SQLite database for local storage
- Background price scheduler
- REST API endpoints
- Basic tkinter GUI
- Web UI support

### Features
- Multi-asset support (stocks, forex, crypto)
- Automatic price updates every 5 minutes
- mDNS discovery via tickertronixhub.local
- Device management for connected displays

## [1.0.0] - Initial Release

### Added
- Core Raspberry Pi Hub functionality
- Alpaca free-tier API integration
- Local HTTP API server
- Basic GUI for asset selection
- Automated setup script
- systemd service configuration

---

[1.1.0]: https://github.com/Tickertronix/Tickertronix-Open/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/Tickertronix/Tickertronix-Open/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Tickertronix/Tickertronix-Open/releases/tag/v1.0.0
