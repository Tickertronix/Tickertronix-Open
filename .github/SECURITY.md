# Security Policy

## Supported Versions
Currently supported: v1.0.0+

## Reporting a Vulnerability
**DO NOT** open public issues for security vulnerabilities.

Contact: Open a private security advisory via GitHub
- Expected response: 48-72 hours
- Include: Component, vulnerability description, reproduction steps

## Security Considerations
- Pi Hub runs on local network only (no internet exposure)
- API credentials stored in SQLite (recommend encryption at rest)
- Devices support HMAC-SHA256 authentication option
- Never expose port 5001 to internet without authentication
- Change default Pi credentials immediately after setup

## Known Limitations
- Default hub API has no authentication (designed for local LAN)
- SQLite credentials not encrypted by default
- mDNS exposes hostname on local network
