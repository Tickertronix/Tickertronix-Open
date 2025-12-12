# Tickertronix Hub (Raspberry Pi)

A local financial data hub that turns any Raspberry Pi into a market data server for your LAN. Fetches real-time prices from Alpaca's free-tier API and exposes them via HTTP.

**Tested on:** Raspberry Pi Zero 2 W with Raspberry Pi OS Lite (Bookworm, 64-bit)

## Features

- **Headless Operation** - Runs as a background service, no monitor needed
- **Multi-Asset Support** - Track stocks, forex, and crypto (up to 50 assets per class)
- **Automatic Updates** - Background scheduler fetches prices every 5 minutes
- **Local Database** - SQLite storage for credentials and price history
- **HTTP API** - REST endpoints accessible from any device on your network
- **mDNS Discovery** - Access via `tickertronixhub.local` (or your DNS A record); mDNS is best-effort, DNS is recommended for stability
- **Free Tier Only** - Uses Alpaca's free market data API

## Quick Start (Recommended)

### Prerequisites

1. **Raspberry Pi** with Raspberry Pi OS Lite (Bookworm, 64-bit) installed
2. **SSH access** or keyboard/monitor connected
3. **Internet connection** (WiFi or Ethernet)
4. **Alpaca account** with API credentials from https://alpaca.markets

### One-Command Setup

SSH into your Pi, then run:

```bash
# Clone the repository
git clone https://github.com/Tickertronix/Tickertronix-Open.git
cd Tickertronix-Open/raspberry-pi-hub

# Run the setup script
sudo ./setup.sh
```

The setup script will:
- Install all system dependencies
- Set the hostname to `tickertronixhub` (works with `.local` mDNS and DNS A-records)
- Create a Python virtual environment
- Install the systemd service
- Create the `tickertronix` CLI helper

### Configure Credentials

```bash
tickertronix setup-credentials
```

Enter your Alpaca API Key and Secret when prompted.

### Start the Service

`setup.sh` installs, enables, and starts the `tickertronix-hub` systemd service automatically. Use the helper to check or manage it:

```bash
tickertronix status    # view service status
tickertronix restart   # restart after config changes
tickertronix stop      # stop temporarily
```

### Access Your Hub

From any device on your network:
```bash
curl http://tickertronixhub.local:5001/health
curl http://tickertronixhub.local:5001/prices
```

Reliable, collision-proof addressing (recommended):
1. Reserve the Pi's IP in your router (DHCP reservation).
2. Add a DNS A record on your router for `tickertronixhub.local` pointing to that IP (or use `tickertronixhub.lan` if your router dislikes `.local`).
3. Set `HUB_BASE_HOST` so the UI links use that deterministic name:
   ```bash
   echo "HUB_BASE_HOST=tickertronixhub.local" | sudo tee -a /opt/tickertronix-hub/.env
   sudo systemctl restart tickertronix-hub
   ```

---

## Manual Installation

If you prefer to install manually or on a non-Pi system:

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-tk git
```

### 2. Clone the Repository

```bash
git clone https://github.com/Tickertronix/Tickertronix-Open.git
cd Tickertronix-Open/raspberry-pi-hub
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

If you used `setup.sh`, this is already configured. For manual installs, create a systemd service so the hub starts when your Raspberry Pi boots:

1. Create a systemd service file:

```bash
sudo nano /etc/systemd/system/raspberry-pi-hub.service
```

2. Add the following content (adjust paths as needed):

```ini
[Unit]
Description=Raspberry Pi Hub
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/raspberry-pi-hub
ExecStart=/usr/bin/python3 /home/pi/raspberry-pi-hub/main.py
Restart=always
RestartSec=10
Environment="DISPLAY=:0"

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable raspberry-pi-hub
sudo systemctl start raspberry-pi-hub
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
raspberry-pi-hub/
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

Price history is automatically trimmed to the last **7 days**. A daily cleanup job runs inside the hub, and you can invoke it manually if needed:

```bash
python3 scripts/cleanup_price_history.py
```

## CLI Commands

After running `setup.sh`, the `tickertronix` command is available:

| Command | Description |
|---------|-------------|
| `tickertronix start` | Start the hub service |
| `tickertronix stop` | Stop the hub service |
| `tickertronix restart` | Restart the hub service |
| `tickertronix status` | Show service status |
| `tickertronix logs` | Follow application logs |
| `tickertronix setup-credentials` | Configure Alpaca API keys |

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
