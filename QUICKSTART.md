# Quick Start Guide

## Installation (5 minutes)

1. **Run the installation script:**
   ```bash
   cd ~/alpaca-price-hub
   ./install.sh
   ```

2. **Get your Alpaca API credentials:**
   - Sign up at https://alpaca.markets (free)
   - Go to Dashboard → Your API Keys
   - Copy your API Key ID and Secret Key

## First Run

1. **Start the application:**
   ```bash
   ./start.sh
   ```
   Or:
   ```bash
   python3 main.py
   ```

2. **Enter your credentials:**
   - Paste your Alpaca API Key ID
   - Paste your Alpaca API Secret Key
   - Click "Save & Verify"

3. **Select assets to track:**
   - Browse available stocks, forex, and crypto
   - Use Ctrl+Click to select multiple (up to 35 per class)
   - Click "Save Selections & Start Updates"

4. **View prices:**
   - Switch to "Status & Prices" tab
   - Prices update every 5 minutes
   - See opening price, last price, change amount, and change %

## Using the API

Find your Raspberry Pi's IP address:
```bash
hostname -I
```

Access from any device on your network:
```bash
# Health check
curl http://192.168.1.100:5001/health

# Get all prices
curl http://192.168.1.100:5001/prices

# Get stock prices
curl http://192.168.1.100:5001/prices/stocks

# Get specific stock
curl http://192.168.1.100:5001/prices/stocks/AAPL
```

## Files & Locations

- **Database:** `data/prices.db`
- **Logs:** `logs/app.log`
- **Config:** `config.py`

## Troubleshooting

**GUI won't start?**
- Make sure you're running Raspberry Pi OS with desktop
- Try: `DISPLAY=:0 python3 main.py`

**Can't verify credentials?**
- Check your API key and secret (no spaces)
- Ensure internet connection
- Check `logs/app.log` for errors

**No prices showing?**
- Make sure you clicked "Save Selections & Start Updates"
- Wait up to 5 minutes for first update
- Check Status tab to verify scheduler is running

**Can't access API from other devices?**
- Ensure both devices are on same network
- Check if port 5001 is open
- Test locally first: `curl http://localhost:5001/health`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Configure update interval in `config.py`
- Set up autostart (see README.md)
- Build your own apps using the HTTP API!
