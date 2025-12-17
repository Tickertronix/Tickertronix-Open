# Tickertronix Releases

This directory contains all versioned releases for the Tickertronix project.

## Directory Structure

```
releases/
├── v1.1.0/          # Version 1.1.0 release (latest)
│   ├── tickertronix-hub-v1.1.0.tar.gz
│   ├── tickertronix-hub-v1.1.0.zip
│   ├── matrix-portal-single-v1.1.0.zip
│   ├── matrix-portal-scroll-v1.1.0.zip
│   └── *.sha256     # Checksums for all archives
├── v1.0.1/          # Version 1.0.1 release (if exists)
└── v1.0.0/          # Version 1.0.0 release (if exists)
```

## Latest Release: v1.1.0

See [v1.1.0/README.md](v1.1.0/README.md) for complete details.

**Quick Download:**
- [Raspberry Pi Hub](https://github.com/Tickertronix/Tickertronix-Open/releases/download/v1.1.0/tickertronix-hub-v1.1.0.tar.gz)
- [Matrix Portal Single](https://github.com/Tickertronix/Tickertronix-Open/releases/download/v1.1.0/matrix-portal-single-v1.1.0.zip)
- [Matrix Portal Scroll](https://github.com/Tickertronix/Tickertronix-Open/releases/download/v1.1.0/matrix-portal-scroll-v1.1.0.zip)

## Building Releases

### Raspberry Pi Hub
```bash
cd raspberry-pi-hub
./scripts/create_release.sh 1.1.0
```

### Matrix Portal Firmwares
```bash
cd /path/to/tickertronix-open
./scripts/create_firmware_releases.sh 1.1.0
```

All release artifacts will be placed in `releases/v{VERSION}/`

---

For more information, visit the [main project](https://github.com/Tickertronix/Tickertronix-Open).
