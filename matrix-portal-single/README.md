# Matrix Portal Single - Single-Asset LED Matrix Display

Single-panel (64×32) Matrix Portal S3 display that shows one asset at a time, cycling through your watchlist with configurable dwell time.

## Overview

The Matrix Portal Single provides a full-screen display for individual assets on a single 64×32 LED matrix panel. Unlike the scrolling display, this version shows complete asset information (symbol, name, price, change) for one asset at a time before transitioning to the next. Perfect for desk setups where you want to focus on one stock at a time.

### Features

- **Full-Screen Single-Asset Display** - Dedicated view for each asset
- **Configurable Dwell Time** - Default 2.5s per asset, fully customizable
- **Asset Class Ordering** - Control whether stocks, crypto, or forex appear first
- **Minimal Flicker** - Hard cut transitions for smooth viewing
- **4-Color Palette** - Black/white/green/red for clear price indication
- **WiFi Provisioning** - Easy setup via captive portal
- **Local Hub Mode** - Connects directly to your Tickertronix Hub
- **3D Printable Enclosure** - STL files included

---

## Hardware Requirements

### Required Components

1. **Adafruit Matrix Portal S3**
   - CircuitPython-compatible board
   - Built-in WiFi
   - **Adafruit Product ID**: #5778
   - **Price**: ~$25
   - **Buy**: https://www.adafruit.com/product/5778

2. **64x32 RGB LED Matrix Panel** (Single Panel)
   - 3mm or 4mm pitch
   - HUB75 interface
   - 1/16 scan rate recommended
   - **Adafruit Product ID**: #2278 (3mm) or #2277 (4mm)
   - **Price**: ~$25-35
   - **Buy**: https://www.adafruit.com/product/2278

3. **5V Power Supply**
   - Minimum 2A for single panel
   - 4A recommended for brightness headroom
   - **Adafruit Product ID**: #1466 (5V/4A)
   - **Buy**: https://www.adafruit.com/product/1466

4. **Cables**
   - USB-C cable for Matrix Portal programming
   - Power cable with barrel jack (usually included with PSU)

### Optional Components

- **3D Printed Enclosure** - STL files in `3D Files/` directory
- **Mounting Hardware** - For wall or desk mounting

---

## Software Prerequisites

### CircuitPython Installation

1. **Download CircuitPython** for Matrix Portal S3:
   - Version 9.0.0+ recommended
   - Download from: https://circuitpython.org/board/matrixportal_s3/

2. **Install CircuitPython**:
   - Connect Matrix Portal to computer via USB-C
   - Double-click RESET button (D0) to enter bootloader mode
   - Drag downloaded .UF2 file to BOOT drive
   - Device will reboot as CIRCUITPY drive

### Required Libraries

Install these CircuitPython libraries to the `/lib/` directory on CIRCUITPY:

**Required**:
- `adafruit_requests.mpy`
- `adafruit_ticks.mpy`
- `adafruit_bitmap_font/` (folder)
- `adafruit_display_text/` (folder)
- `adafruit_matrixportal/` (folder)
- `adafruit_portalbase/` (folder)

**Download from**:
- CircuitPython Library Bundle: https://circuitpython.org/libraries
- Match bundle version to your CircuitPython version

---

## Wiring Diagram

### Matrix Panel to Matrix Portal Connection

The Matrix Portal S3 plugs directly into the matrix panel's HUB75 connector:

```
Matrix Panel HUB75 Input
    ┌─────────────┐
    │ R1 G1 B1 E  │
    │ R2 G2 B2 GND│
    │ A  B  C  D  │
    │ CLK LAT OE  │
    │ GND         │
    └──────┬──────┘
           │
    ┌──────┴──────┐
    │Matrix Portal│
    │     S3      │
    └─────────────┘
```

### Power Connections

1. **Matrix Panel**: Connect 5V power supply to panel's power input
2. **Matrix Portal**: Powered via USB-C (for programming) or panel's 5V rail
3. **Ground**: Ensure common ground between panel and power supply

**IMPORTANT**: Do not power the Matrix Portal from computer USB while the panel is powered - this can damage your computer's USB port. Use external 5V supply.

---

## Installation

### Fast install (drag-and-drop)
- Grab `matrix-portal-single.zip` from GitHub Releases (or build with `./scripts/build_matrix_portal_releases.sh`) and unzip directly to the `CIRCUITPY` drive (overwrite existing files). This includes `code.py`, support modules, fonts, and expected `lib/` deps.

### Step 1: Prepare Matrix Portal

1. Install CircuitPython on Matrix Portal S3
2. Create `/lib/` directory on CIRCUITPY
3. Copy required libraries to `/lib/`
4. Copy `fonts/` directory to CIRCUITPY root

### Step 2: Deploy Code Files

Copy the following files to CIRCUITPY root:

```
CIRCUITPY/
├── code.py              # Main display loop
├── api_client.py        # Hub API client
├── boot.py              # Provisioning switch check
├── wifimgr.py          # WiFi manager
├── provisioning_v2.py  # Provisioning portal
├── fonts/
│   └── spleen-8x16.bdf  # Required font
└── lib/                 # CircuitPython libraries
    ├── adafruit_requests.mpy
    ├── adafruit_ticks.mpy
    └── ... (other libraries)
```

### Step 3: Font Installation

**Required Font**: `spleen-8x16.bdf`

This font provides clear, readable text on the 64×32 panel.

**Install**:
- Copy `fonts/spleen-8x16.bdf` to `CIRCUITPY/fonts/`
- Ensure path is exactly: `/fonts/spleen-8x16.bdf`

**Alternative Fonts**:
You can use other BDF fonts, but update `code.py`:
```python
font = bitmap_font.load_font("/fonts/your-font.bdf")
```

---

## Provisioning

### Initial Setup

On first boot (or after factory reset), the device enters provisioning mode:

1. **Ground A1 Pin** on Matrix Portal while powering on
2. **Connect to WiFi Network**: "TickerSetup" (open network)
3. **Navigate to**: http://192.168.4.1 in browser
4. **Provisioning Portal Opens**:
   - Enter your WiFi SSID
   - Enter WiFi password
   - Enter Hub URL: `http://tickertronixhub.local:5001`
     - Or use direct IP: `http://192.168.1.XXX:5001`
5. **Click "Save"**
6. **Reboot**: Remove A1 ground and reset

### Normal Operation

After provisioning:
1. Remove A1 ground connection
2. Reset or power cycle
3. Device connects to WiFi
4. Fetches data from Hub
5. Begins displaying assets

### Factory Reset

To re-provision or change settings:
1. Ground A1 pin
2. Power on or reset
3. Follow provisioning steps above

---

## Configuration

### Dwell Time

Control how long each asset displays before advancing:

**Edit `code.py`**:
```python
# Line ~15
ITEM_DWELL_SEC = 2.5  # Seconds per asset

# Change to 5 seconds:
ITEM_DWELL_SEC = 5.0
```

### Asset Order

Control which asset class displays first:

**Edit `code.py`**:
```python
# Line ~18
ASSET_ORDER = ['stocks', 'crypto', 'forex']

# Show crypto first:
ASSET_ORDER = ['crypto', 'stocks', 'forex']

# Only stocks:
ASSET_ORDER = ['stocks']
```

### Hub URL

Set via provisioning portal OR manually in `device_config.json`:

**Create or edit `device_config.json` on CIRCUITPY**:
```json
{
  "hub_base_url": "http://tickertronixhub.local:5001",
  "device_key": "unused-for-local-mode"
}
```

---

## 3D Printed Enclosure

STL files included in `3D Files/` directory:

### Print Settings

- **Material**: PLA or PETG
- **Layer Height**: 0.2mm
- **Infill**: 15-20%
- **Supports**: Yes (for overhangs)
- **Print Time**: ~6-8 hours total

### Assembly

1. Print enclosure parts
2. Install Matrix Panel in front bezel
3. Mount Matrix Portal to panel
4. Route power cables
5. Snap or screw rear cover
6. Add rubber feet or mounting brackets

---

## Troubleshooting

### No Display / Blank Screen

**Symptoms**: Panel powers on but shows no data

**Solutions**:
- Verify CircuitPython installed correctly
- Check `boot_out.txt` for CircuitPython version
- Ensure all required libraries in `/lib/`
- Verify `fonts/spleen-8x16.bdf` exists
- Check serial console for errors: `screen /dev/ttyACM0 115200`

### "No Data" Message

**Symptoms**: Panel shows "No Data" instead of prices

**Solutions**:
- Verify Hub is running: `curl http://tickertronixhub.local:5001/health`
- Check Hub has assets selected and credentials configured
- Verify WiFi connection (check router)
- Confirm `device_config.json` has correct Hub URL
- Check Hub logs: `journalctl -u tickertronix-hub -f`

### Flicker or Ghosting

**Symptoms**: Display flickers or shows ghost images

**Solutions**:
- Reduce brightness in code (`display.brightness = 0.5`)
- Use shorter, higher-quality power cables
- Ensure adequate power supply (2A minimum)
- Check for loose HUB75 connection

### WiFi Won't Connect

**Symptoms**: Device stuck in provisioning mode

**Solutions**:
- Verify WiFi credentials (SSID and password are case-sensitive)
- Ensure 2.4GHz WiFi network (Matrix Portal doesn't support 5GHz)
- Check router settings (WPA2 supported, not WPA3-only)
- Move device closer to WiFi access point
- Factory reset and re-provision

### Provisioning Portal Won't Load

**Symptoms**: Can't access http://192.168.4.1

**Solutions**:
- Ensure A1 pin is grounded during boot
- Confirm device created "TickerSetup" network
- Check your computer connected to "TickerSetup" WiFi
- Try different browser (Chrome/Firefox recommended)
- Disable VPN or firewall temporarily

### Font Not Loading

**Symptoms**: Blank display or font error in console

**Solutions**:
- Verify `fonts/spleen-8x16.bdf` exists on CIRCUITPY
- Check file path in code matches exactly
- Re-copy font file from source repository
- Try alternative BDF font

### Panel Powers On But No Data Updates

**Symptoms**: Shows old prices or doesn't refresh

**Solutions**:
- Check Hub is updating prices: `curl http://tickertronixhub.local:5001/prices`
- Verify Hub scheduler running: `tickertronix status`
- Check device WiFi connection
- Restart Matrix Portal (press RESET button)
- Check serial console for API errors

---

## Development

### Serial Console Debugging

Connect via USB and monitor serial output:

**Linux/Mac**:
```bash
screen /dev/ttyACM0 115200
```

**Windows**: Use PuTTY or Arduino Serial Monitor

**Sample Output**:
```
[WiFi] Connecting to MyNetwork...
[WiFi] Connected! IP: 192.168.1.142
[API] Fetching: http://tickertronixhub.local:5001/prices
[API] Response: 200
[Display] Stocks: 5, Crypto: 3, Forex: 2
[Display] Showing: AAPL at $178.32
[Cycle] Waiting 2.5s before next asset
```

### API Integration

The device expects JSON from the Hub in this format:

```json
{
  "stocks": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc",
      "price": 178.32,
      "change": 2.45,
      "change_percent": 1.39
    }
  ],
  "crypto": [...],
  "forex": [...]
}
```

**API Client**: See `api_client.py` for implementation details

### Customizing Display

**Colors**:
Edit color constants in `code.py`:
```python
COLOR_BLACK = 0x000000
COLOR_WHITE = 0xFFFFFF
COLOR_GREEN = 0x00FF00  # Positive change
COLOR_RED = 0xFF0000    # Negative change
```

**Layout**:
Modify the `displayAsset()` function in `code.py` to change:
- Text positions
- Font sizes
- Information displayed
- Transition effects

---

## File Structure

```
matrix-portal-single/
├── code.py                # Main display loop
├── api_client.py          # Hub API client
├── boot.py                # Provisioning switch check
├── wifimgr.py            # WiFi management
├── provisioning_v2.py    # Provisioning web portal
├── fonts/
│   └── spleen-8x16.bdf   # Display font
├── lib/                  # CircuitPython libraries (copied by user)
│   ├── adafruit_requests.mpy
│   ├── adafruit_ticks.mpy
│   └── ... (others)
├── 3D Files/             # Printable enclosure
│   ├── Frame.stl
│   ├── Back.stl
│   └── Stand.stl
└── README.md             # This file
```

---

## Comparison to Matrix Portal Scroll

| Feature | Single | Scroll |
|---------|--------|--------|
| Panels | 1 | 1-6 |
| Display Mode | One asset at a time | Continuous scroll |
| Asset Information | Full (symbol, name, price, change) | Compact (symbol, price) |
| Transition | Hard cut | Smooth scroll |
| Dwell Time | Configurable (2.5s default) | N/A (continuous) |
| Best For | Desk/close viewing | Wall/ambient |
| Power | 2A | 2A-8A (depends on panel count) |

---

## Technical Specifications

| Spec | Value |
|------|-------|
| Display | 64×32 RGB LED Matrix |
| Microcontroller | ESP32-S3 (Matrix Portal S3) |
| WiFi | 2.4GHz 802.11 b/g/n |
| Firmware | CircuitPython 9.0+ |
| Power | 5V/2A minimum |
| Refresh Rate | ~60 Hz |
| Color Depth | 24-bit RGB |
| Update Interval | Hub fetch every 30s |

---

## Future Enhancements

- Multi-asset per screen (2x2 grid)
- Chart/graph visualization
- Animated transitions
- Brightness auto-adjustment
- Custom color schemes
- Alert indicators
- Time/date display option

---

## Contributing

See main repository [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## License

MIT License - see [LICENSE](../LICENSE)

---

## Support

- **Issues**: [GitHub Issues](https://github.com/Tickertronix/Tickertronix-Open/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Tickertronix/Tickertronix-Open/discussions)
- **Documentation**: See [root README](../README.md)
