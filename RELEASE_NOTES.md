# Release Notes - v1.1.0

## Highlights
- **Raspberry Pi Hub**: Local REST API server (port 5001) with SQLite-backed credentials, mDNS discovery, five-minute refresh cadence, and a web UI for configuration. Supports Alpaca (stocks/crypto) and Twelve Data (forex) without cloud dependencies, with HMAC-secured device communication on the LAN.
- **Matrix Portal Scroll**: CircuitPython firmware for smooth scrolling tickers across 1–6 chained 64x32 RGB panels, with captive-portal WiFi provisioning, customizable fonts and scroll speed, and a 3D-printable multi-panel enclosure.
- **Matrix Portal Single**: Single-asset full-screen display for a single 64x32 panel, featuring configurable dwell time, asset-class ordering, flicker-resistant transitions, and printable enclosure parts.
- **CYD Ticker (ESP32-2432S028R)**: Touchscreen-driven provisioning and watchlist browsing on a 320x240 ILI9341 display, including retro-styled UI, color-coded change indicators, SD card logging, and optional retro enclosure.
- **Release automation**: GitHub Actions build release bundles automatically on version tags, with unified versioning and consistent asset names for all devices.

## Release assets
- `tickertronix-matrix-portal-scroll-v1.1.0.zip` — CircuitPython bundle (libraries, fonts) for scrolling ticker builds.
- `tickertronix-matrix-portal-single-v1.1.0.zip` — CircuitPython bundle for the single-asset Matrix Portal build.
- `tickertronix-raspberry-pi-hub-v1.1.0.tar.gz` — Raspberry Pi Hub source tarball with automated setup script (`sudo ./setup.sh`).
- `tickertronix-cyd-ticker-source-v1.1.0.zip` — Arduino source bundle for the Cheap Yellow Display ticker.

## How to publish the release
1. **Finalize notes**: Confirm `CHANGELOG.md` and this file reflect v1.1.0, and keep `[Unreleased]` empty or updated for future work.
2. **(Optional) Build artifacts locally**: Generate device bundles before tagging:
   - `./scripts/build_matrix_portal_releases.sh 1.1.0`
   - `./scripts/build_pi_hub_release.sh 1.1.0`
   - `./scripts/build_cyd_source_release.sh 1.1.0`
3. **Tag and push**: Tag the release commit and push the tag to trigger the automated GitHub Actions build: `git tag v1.1.0 && git push origin v1.1.0`.
4. **Publish on GitHub**: After the workflow attaches artifacts, draft the GitHub Release for tag `v1.1.0`, paste these notes, and verify assets (`tickertronix-*-v1.1.0.*`) appear on the page.
