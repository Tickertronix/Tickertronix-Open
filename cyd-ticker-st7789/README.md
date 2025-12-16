# CYD Ticker (Cheap Yellow Display)

![CYD Ticker demo](../assets/cyd-ticker-il9341/demo.png)

Real-time financial ticker display for the ESP32-2432S028R "Cheap Yellow Display" with touchscreen provisioning and retro-styled UI.

## Overview

The CYD Ticker transforms the affordable ESP32-2432S028R (~$15) into a standalone market data display with touchscreen controls. Features a retro-inspired UI with color-coded price changes and smooth transitions between assets.

### Features

- **320x240 ILI9341 Touchscreen Display** - Interactive UI with touch controls
- **WiFi Provisioning** - Touch-based setup portal (no code changes needed)
- **Local Hub Mode** - Connects directly to your Tickertronix Hub on LAN
- **Multi-Asset Cycling** - Automatically rotates through stocks, crypto, and forex
- **Retro UI Design** - Color-coded indicators (green/red for changes)
- **NTP Time Sync** - Accurate timestamps from NTP servers
- **SD Card Support** - Optional logging and configuration storage
- **3D Printable Case** - Retro-styled enclosure with viewing stand

---

## Hardware Requirements

### Required Components

1. **ESP32-2432S028R Board** (Cheap Yellow Display / CYD)
   - ESP32 microcontroller
   - 320x240 ILI9341 TFT display
   - XPT2046 resistive touchscreen
   - Built-in USB-C programming/power
   - **Where to buy**: AliExpress, Amazon (~$12-18)
   - **Search terms**: "ESP32-2432S028R", "ESP32 2.8 inch display", "Cheap Yellow Display"

2. **USB-C Cable**
   - For programming and power
   - Any standard USB-C cable

3. **5V Power Supply** (Optional)
   - Can run from USB power (computer/wall adapter)
   - 500mA+ recommended

### Optional Components

- **MicroSD Card** - For logging/config storage (not required)
- **3D Printed Case** - STL files included in `3D Files/` directory

---

## Pinout Reference

The ESP32-2432S028R has the following configuration (handled automatically by the code):

### Display (ILI9341 TFT)
- Managed by TFT_eSPI library
- Configuration in `TFT_eSPI` User_Setup.h

### Touchscreen (XPT2046)
- IRQ: GPIO 36
- MOSI: GPIO 32
- MISO: GPIO 39
- CLK: GPIO 25
- CS: GPIO 33

### SD Card (Optional)
- CS: GPIO 5
- MOSI: GPIO 23
- MISO: GPIO 19
- SCK: GPIO 18

---

## Software Setup

### Prerequisites

1. **Arduino IDE** (1.8.19+) or **PlatformIO**
2. **ESP32 Board Support**
   - Arduino IDE: Add ESP32 board manager URL
   - `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Install "ESP32 by Espressif Systems"

3. **Required Libraries** (Install via Library Manager):
   - `TFT_eSPI` (2.5.0+)
   - `WiFi` (included with ESP32 core)
   - `HTTPClient` (included with ESP32 core)
   - `Preferences` (included with ESP32 core)
   - `SD` (included with ESP32 core)
   - `ArduinoJson` (for JSON parsing)

### TFT_eSPI Configuration

**CRITICAL**: Firmware is identical across CYD variants; the only difference is the TFT_eSPI `User_Setup.h`. Use the included `User_Setup_ST7789.h` with this build.

1. **Locate TFT_eSPI Library**  
   - Arduino: `Documents/Arduino/libraries/TFT_eSPI/`  
   - PlatformIO: `.pio/libdeps/[env]/TFT_eSPI/`

2. **Replace `User_Setup.h`**  
   - Backup the existing `User_Setup.h` (e.g., rename to `User_Setup_original.h`).  
   - Copy this repo’s `User_Setup_ST7789.h` into the TFT_eSPI folder and rename it to `User_Setup.h`.

3. **Ensure it is selected**  
   - Open `User_Setup_Select.h` in the same folder.  
   - Comment out all other `#include <User_Setups/...>` lines.  
   - Leave `#include <User_Setup.h>` uncommented so your renamed file is the active setup.

4. **Rebuild and upload**  
   - Recompile and flash. A white screen or inverted colors usually means the wrong `User_Setup.h` is being used.

---

## Installation

### Step 1: Prepare Hardware

1. Connect CYD to computer via USB-C cable
2. Device should appear as COM/serial port
3. Note: No external wiring required

### Step 2: Upload Firmware

**Using Arduino IDE:**

1. Open `CYD_Complete_System/CYD_Complete_System.ino`
2. Select board: **Tools → Board → ESP32 Arduino → ESP32 Dev Module**
3. Select port: **Tools → Port → [Your COM port]**
4. Configure board settings:
   - Flash Size: 4MB
   - Partition Scheme: Default
   - Upload Speed: 115200 (or 921600 if supported)
5. Click **Upload** (→)
6. Wait for compilation and upload (~2-3 minutes)

**Using PlatformIO:**

```bash
cd cyd-ticker-il9341/CYD_Complete_System
pio run --target upload
```

### Step 3: Initial Provisioning

On first boot, the device will automatically enter provisioning mode:

1. **Display shows**: "Touch to Configure WiFi"
2. **Touch screen** to enter setup
3. **WiFi Provisioning UI appears**:
   - Touch keyboard to enter SSID
   - Touch keyboard to enter WiFi password
   - Touch keyboard to enter Hub URL
     - Format: `http://tickertronixhub.local:5001`
     - Or use IP: `http://192.168.1.XXX:5001`
4. **Touch "Save & Connect"**
5. Device will:
   - Save WiFi credentials to flash memory
   - Connect to WiFi
   - Verify Hub connection
   - Begin displaying market data

### Step 4: Verify Operation

Once provisioned:
- Screen shows current asset with price
- Green background = price increase
- Red background = price decrease
- Automatically cycles through assets every few seconds
- Top bar shows connection status and time

---

## Usage

### Normal Operation

After provisioning, the device operates autonomously:

1. **Auto-start**: Powers on and connects to WiFi automatically
2. **Data Fetch**: Pulls price data from Hub every 30 seconds
3. **Display Cycle**: Rotates through all tracked assets
4. **Time Sync**: Updates from NTP servers hourly

### Display Layout

```
┌─────────────────────────────────┐
│ [WiFi] AAPL     14:35:22  [Hub] │ ← Status Bar
├─────────────────────────────────┤
│                                 │
│         AAPL                    │ ← Symbol
│      Apple Inc                  │ ← Company Name
│                                 │
│       $178.32                   │ ← Current Price
│       +2.45 (+1.39%)           │ ← Change (Green/Red)
│                                 │
│   Last Update: 14:35           │ ← Timestamp
│                                 │
└─────────────────────────────────┘
```

### Touch Interactions

- **Single Tap**: Advance to next asset immediately
- **Long Press (3s)**: Enter settings/provisioning mode
- **Factory Reset**: Hold touch during power-on boot

### Settings Mode

Access via long press:
- **Re-provision WiFi**: Change network settings
- **Change Hub URL**: Point to different Hub
- **Display Settings**: Brightness, rotation (future)
- **Exit**: Return to normal display

---

## Configuration

### Hub URL Configuration

The Hub URL tells the CYD where to fetch data:

**Local Network (Recommended):**
```
http://tickertronixhub.local:5001
```

**Direct IP (if mDNS fails):**
```
http://192.168.1.100:5001
```

**Cloud/Remote Hub:**
```
https://your-hub-domain.com
```

### Asset Display Order

Modify in code (`CYD_Complete_System.ino`):
```cpp
// Line ~110
String assetOrder[] = {"stocks", "crypto", "forex"};
int assetOrderSize = 3;
```

### Cycle Timing

Adjust dwell time per asset:
```cpp
// Line ~115
const int DISPLAY_CYCLE_MS = 5000;  // 5 seconds per asset
```

### Display Colors

Customize color scheme (line ~54):
```cpp
#define BG_COLOR TFT_BLACK
#define TEXT_COLOR TFT_WHITE
#define GREEN_COLOR TFT_GREEN      // Positive change
#define RED_COLOR TFT_RED          // Negative change
#define BLUE_COLOR TFT_CYAN        // Neutral/info
```

---

## 3D Printed Enclosure

STL files included in `3D Files/` directory:

### Files
- `Retro Ticker Frame V7.stl` - Main front bezel
- `Retro Ticker Holder V7.stl` - Angled stand/holder
- `Retro Ticker Back V7.stl` - Rear cover/backplate

### Print Settings
- **Material**: PLA or PETG
- **Layer Height**: 0.2mm
- **Infill**: 15-20%
- **Supports**: Required for Holder piece
- **Print Time**: ~8-12 hours total

### Assembly
1. Print all three pieces
2. Insert CYD into frame (friction fit)
3. Snap on back cover
4. Place in angled holder for desk display
5. Route USB-C cable through holder slot

---

## Troubleshooting

### Upload Issues

**Problem**: "Failed to connect to ESP32"
- **Solution**: Hold BOOT button while clicking Upload
- **Solution**: Try lower upload speed (115200)
- **Solution**: Check USB cable (must support data, not just power)

**Problem**: "Brownout detector triggered"
- **Solution**: Use better power supply (stable 5V/1A+)
- **Solution**: Shorter USB cable
- **Solution**: Add decoupling capacitor if persistent

### Display Issues

**Problem**: White/blank screen
- **Solution**: Verify TFT_eSPI configuration
- **Solution**: Check User_Setup.h pin definitions
- **Solution**: Reflash firmware

**Problem**: Touchscreen not responding
- **Solution**: Run touch calibration (triggered on first boot)
- **Solution**: Verify XPT2046 pins in code
- **Solution**: Check for physical screen damage

**Problem**: Colors inverted/wrong
- **Solution**: Add `#define TFT_INVERSION_ON` to User_Setup.h
- **Solution**: Or `#define TFT_INVERSION_OFF`

### WiFi/Network Issues

**Problem**: Won't connect to WiFi
- **Solution**: Re-provision (long press screen)
- **Solution**: Check WiFi password (case-sensitive)
- **Solution**: Verify 2.4GHz network (CYD doesn't support 5GHz)
- **Solution**: Check router MAC filtering

**Problem**: Can't reach Hub
- **Solution**: Verify Hub is running: `curl http://tickertronixhub.local:5001/health`
- **Solution**: Ping Hub from computer to verify network connectivity
- **Solution**: Try IP address instead of .local hostname
- **Solution**: Check firewall rules (port 5001 must be open)

**Problem**: "No Data" displayed
- **Solution**: Ensure Hub has valid API credentials configured
- **Solution**: Verify Hub has assets selected (stocks/crypto/forex)
- **Solution**: Check Hub logs: `journalctl -u tickertronix-hub -f`

### Data Display Issues

**Problem**: Prices not updating
- **Solution**: Check Hub scheduler status (should auto-start)
- **Solution**: Verify Hub API response: `curl http://tickertronixhub.local:5001/prices`
- **Solution**: Check CYD serial monitor for error messages

**Problem**: Only some assets display
- **Solution**: Verify all asset types have data in Hub
- **Solution**: Check Hub asset selection includes desired symbols

---

## Development

### Serial Monitor Debugging

Connect to serial port at 115200 baud to see debug output:

```
=== CYD Ticker Starting ===
[WiFi] Connecting to MyNetwork...
[WiFi] Connected! IP: 192.168.1.150
[NTP] Syncing time...
[NTP] Time synced: 2025-12-11 14:35:22
[API] Fetching from http://tickertronixhub.local:5001/prices
[API] Response code: 200
[API] Stocks: 5, Crypto: 3, Forex: 2
[Display] Showing AAPL: $178.32 (+1.39%)
```

### API Response Format

Expected JSON from Hub:
```json
{
  "stocks": [
    {"symbol": "AAPL", "name": "Apple Inc", "price": 178.32, "change": 2.45, "change_percent": 1.39}
  ],
  "crypto": [
    {"symbol": "BTC/USD", "name": "Bitcoin", "price": 45230.10, "change": -342.50, "change_percent": -0.75}
  ],
  "forex": [
    {"symbol": "EUR/USD", "name": "Euro/US Dollar", "price": 1.0823, "change": 0.0012, "change_percent": 0.11}
  ]
}
```

### HMAC Authentication (Future)

Current implementation uses local hub mode (no authentication). For cloud/remote access, HMAC authentication is available via `hmac_auth.cpp/h`.

**To enable**:
1. Set `localHubMode = false` in code
2. Configure provisioning key on Hub
3. Provision device with PROV key
4. HMAC headers added automatically to API requests

---

## Technical Specifications

| Spec | Value |
|------|-------|
| Microcontroller | ESP32-WROOM-32 |
| Display | ILI9341 320x240 TFT |
| Touch | XPT2046 Resistive |
| WiFi | 2.4GHz 802.11 b/g/n |
| Power | 5V USB-C, ~150-250mA |
| Flash | 4MB |
| RAM | 520KB |
| Operating Temp | 0-50°C |

---

## File Structure

```
cyd-ticker-il9341/
├── CYD_Complete_System/
│   ├── CYD_Complete_System.ino    # Main firmware
│   ├── api_functions.ino          # Hub API client
│   ├── device_settings.ino        # Provisioning & config
│   ├── provisioning_ui.ino        # Touch keyboard UI
│   ├── hmac_auth.cpp/h            # HMAC authentication
│   └── README.md
├── 3D Files/
│   ├── Retro Ticker Frame V7.stl
│   ├── Retro Ticker Holder V7.stl
│   └── Retro Ticker Back V7.stl
├── hmac_auth.cpp                  # Standalone HMAC (reference)
├── hmac_auth.h
└── README.md                      # This file
```

---

## Future Enhancements

- Multi-page layouts (4 assets per screen)
- Chart/graph visualization
- Alert/notification system
- Battery power support
- Custom watch lists
- Touch-controlled asset selection
- Landscape/portrait rotation
- Dark/light theme toggle

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
