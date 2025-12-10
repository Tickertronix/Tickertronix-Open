# Alpaca Price Hub

A local "price hub" application for Raspberry Pi OS 64-bit that fetches market data from Alpaca's free-tier API and exposes it via a local HTTP API for other devices on your LAN.

## Features

- **Simple GUI** - tkinter-based interface for credentials and asset selection
- **Multi-Asset Support** - Track stocks, forex, and crypto (up to 35 assets per class)
- **Automatic Updates** - Background scheduler fetches prices every 5 minutes
- **Local Database** - SQLite storage for credentials and price history
- **HTTP API** - REST endpoints accessible from other LAN devices
- **Free Tier Only** - Data-only usage of Alpaca's free market data API

## Requirements

- Raspberry Pi running Raspberry Pi OS 64-bit (or any Linux system)
- Python 3.8 or higher
- Internet connection
- Alpaca account with API credentials (free tier)

## Installation

### 1. Install System Dependencies

On Raspberry Pi OS, tkinter should already be installed. If not:

```bash
sudo apt update
sudo apt install python3-tk python3-pip
```

### 2. Clone or Download This Project

```bash
cd ~
# If using git:
git clone <repository-url> alpaca-price-hub
cd alpaca-price-hub

# Or extract the zip file if downloaded
```

### 3. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 4. Get Alpaca API Credentials

1. Sign up for a free Alpaca account at https://alpaca.markets
2. Navigate to your dashboard and generate API keys
3. Make sure you're using the **free tier** (data-only) credentials
4. You'll need:
   - API Key ID
   - API Secret Key

## Usage

### Starting the Application

```bash
python3 main.py
```

Or make it executable:

```bash
chmod +x main.py
./main.py
```

### First-Time Setup

1. **Enter Credentials**
   - When you first launch the app, you'll see the credentials screen
   - Enter your Alpaca API Key ID and Secret Key
   - Click "Save & Verify"
   - The app will verify your credentials with Alpaca

2. **Select Assets**
   - After successful verification, you'll see the asset selection screen
   - Choose up to 35 assets per class (Stocks, Forex, Crypto)
   - Use Ctrl+Click to select multiple assets in each list
   - Click "Save Selections & Start Updates"

3. **Monitor Status**
   - Switch to the "Status & Prices" tab to see:
     - Scheduler status (running/stopped)
     - Last update time
     - Next scheduled update time
     - Latest prices with change amounts and percentages

### Running on Startup (Optional)

To have the price hub start automatically when your Raspberry Pi boots:

1. Create a systemd service file:

```bash
sudo nano /etc/systemd/system/alpaca-price-hub.service
```

2. Add the following content (adjust paths as needed):

```ini
[Unit]
Description=Alpaca Price Hub
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/alpaca-price-hub
ExecStart=/usr/bin/python3 /home/pi/alpaca-price-hub/main.py
Restart=always
RestartSec=10
Environment="DISPLAY=:0"

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable alpaca-price-hub
sudo systemctl start alpaca-price-hub
```

## Local HTTP API

The application exposes a REST API on `http://<raspberry-pi-ip>:5001` that can be accessed from any device on your local network.

### Endpoints

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "database": "ok",
  "scheduler": "running",
  "timestamp": "2024-01-01T12:00:00"
}
```

#### GET /prices

Get all tracked asset prices.

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "asset_class": "stocks",
    "date": "2024-01-01",
    "open_price": 150.0,
    "last_price": 152.5,
    "change_amount": 2.5,
    "change_percent": 1.67,
    "last_updated": "2024-01-01T12:00:00"
  },
  ...
]
```

#### GET /prices/\<asset_class\>

Get prices for a specific asset class.

**Parameters:**
- `asset_class`: One of `stocks`, `forex`, `crypto`

**Example:**
```bash
curl http://192.168.1.100:5001/prices/stocks
```

#### GET /prices/\<asset_class\>/\<symbol\>

Get price for a specific asset.

**Parameters:**
- `asset_class`: One of `stocks`, `forex`, `crypto`
- `symbol`: Asset symbol (e.g., `AAPL`, `EUR/USD`, `BTCUSD`)

**Example:**
```bash
curl http://192.168.1.100:5001/prices/stocks/AAPL
```

**Response:**
```json
{
  "symbol": "AAPL",
  "asset_class": "stocks",
  "date": "2024-01-01",
  "open_price": 150.0,
  "last_price": 152.5,
  "change_amount": 2.5,
  "change_percent": 1.67,
  "last_updated": "2024-01-01T12:00:00"
}
```

#### GET /status

Get scheduler status and information.

**Response:**
```json
{
  "is_running": true,
  "last_update": "2024-01-01T12:00:00",
  "next_update": "2024-01-01T12:05:00",
  "interval_minutes": 5
}
```

#### GET /assets

Get list of selected/tracked assets.

**Query Parameters:**
- `asset_class` (optional): Filter by asset class

**Example:**
```bash
curl http://192.168.1.100:5001/assets?asset_class=stocks
```

## Configuration

You can modify settings in `config.py`:

- `UPDATE_INTERVAL_MINUTES` - How often to fetch prices (default: 5 minutes)
- `MAX_ASSETS_PER_CLASS` - Maximum assets per class (default: 35)
- `API_PORT` - Local API server port (default: 5001)
- `RATE_LIMIT_DELAY` - Delay between API calls (default: 0.5 seconds)

## Project Structure

```
alpaca-price-hub/
├── main.py                 # Entry point
├── ui.py                   # tkinter GUI
├── alpaca_client.py        # Alpaca API client
├── db.py                   # SQLite database operations
├── scheduler.py            # Background price updates
├── api_server.py           # Flask HTTP API
├── config.py               # Configuration constants
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── data/                  # Created at runtime
│   └── prices.db          # SQLite database
└── logs/                  # Created at runtime
    └── app.log            # Application logs
```

## Rate Limits & Free Tier

This application is designed for Alpaca's free-tier market data:

- Uses IEX feed for stock data (free tier)
- Bulk API calls where possible to minimize requests
- Configurable delay between API calls
- Updates every 5 minutes by default (adjustable to 5-15 minutes)

If you hit rate limits, the application will log errors and retry on the next scheduled update.

## Accessing from Other Devices

To access the price data from another device on your LAN:

1. Find your Raspberry Pi's IP address:
   ```bash
   hostname -I
   ```

2. From another device on the same network, access the API:
   ```bash
   # Example: Get all prices
   curl http://192.168.1.100:5001/prices

   # Example: Get stock prices only
   curl http://192.168.1.100:5001/prices/stocks

   # Example: Get specific stock
   curl http://192.168.1.100:5001/prices/stocks/AAPL
   ```

3. Use in your applications:
   ```python
   import requests

   # Get all prices
   response = requests.get('http://192.168.1.100:5001/prices')
   prices = response.json()

   for asset in prices:
       print(f"{asset['symbol']}: ${asset['last_price']} ({asset['change_percent']}%)")
   ```

## Troubleshooting

### GUI doesn't start

- Ensure you're running on Raspberry Pi OS with desktop environment
- Check that tkinter is installed: `python3 -c "import tkinter"`
- Try running with `DISPLAY=:0 python3 main.py`

### API credentials verification fails

- Double-check your API key and secret (no extra spaces)
- Ensure you're using Alpaca API credentials (not just login credentials)
- Verify your internet connection
- Check the logs at `logs/app.log`

### No prices showing up

- Make sure you've selected assets and clicked "Save Selections & Start Updates"
- Check that the scheduler is running (Status tab)
- Wait for the first update (happens within 5 minutes)
- Check logs for any API errors

### Can't access API from other devices

- Ensure your Raspberry Pi's firewall allows incoming connections on port 5001
- Verify both devices are on the same network
- Try accessing from the Pi itself first: `curl http://localhost:5001/health`

## Logs

Application logs are stored in `logs/app.log`. Check this file for detailed information about:

- API requests and responses
- Scheduler activity
- Database operations
- Errors and warnings

## Database

Price data is stored in `data/prices.db` (SQLite). The database includes:

- `config` - API credentials and settings
- `selected_assets` - Your chosen assets to track
- `asset_prices` - Historical price data

You can query it directly if needed:

```bash
sqlite3 data/prices.db "SELECT * FROM asset_prices ORDER BY last_updated DESC LIMIT 10;"
```

## Raspberry Pi (Local Hub)

- For a Pi Zero 2 W friendly install, see `docs/PI_DEPLOY.md`.
- One-command setup: `sudo ./scripts/setup_pi.sh --hostname tickertronixhub` (installs deps, venv, systemd service).
- Default mDNS host: `tickertronixhub.local`, port `5001` → `http://tickertronixhub.local:5001/prices`.
- Systemd service: `tickertronixhub` (logs via `journalctl -u tickertronixhub -f`).

## Security Notes

- This application is designed for use on a **trusted local network**
- The HTTP API has **no authentication** (assumes trusted LAN environment)
- API credentials are stored **unencrypted** in the local database
- Do not expose the API port (5001) to the internet
- Use firewall rules to restrict access if needed

## License

This project is provided as-is for educational and personal use.

## Support

For issues related to:
- **Alpaca API**: See https://alpaca.markets/docs
- **This application**: Check logs at `logs/app.log` and raise an issue

## Credits

Built for Raspberry Pi OS 64-bit using:
- Python 3
- tkinter (GUI)
- Flask (API server)
- APScheduler (background tasks)
- SQLite (database)
- Alpaca Markets API (market data)
