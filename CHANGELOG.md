# Changelog

All notable changes to Tickertronix-Open will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
