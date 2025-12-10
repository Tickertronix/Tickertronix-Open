# Windows PC Testing Guide

## Overview

This guide shows you how to fully test the Alpaca Price Hub on your Windows PC before deploying to Raspberry Pi. The **Web UI version** works perfectly on Windows/WSL and can be accessed via your browser!

## Why Web UI?

✅ **Works on Windows PC** - Access via browser, no X server needed
✅ **Works on WSL** - No GUI complications
✅ **Works on Raspberry Pi** - Same interface everywhere
✅ **Test from any device** - Phone, tablet, another computer on your network
✅ **Identical experience** - What you test on Windows works exactly the same on Pi

## Quick Start (5 Minutes)

### Step 1: Start the Application

```bash
cd /mnt/c/users/timot/tickertronix_complete/alpaca-price-hub
./venv/bin/python main_web.py
```

### Step 2: Open in Browser

On your Windows PC, open your browser and go to:

```
http://localhost:8080
```

### Step 3: Setup Credentials

1. Click "Credentials" in the navigation
2. Enter your Alpaca API credentials
3. Click "Save & Verify"

### Step 4: Select Assets

1. Click "Assets" in the navigation
2. Click "Fetch Available Stocks/Forex/Crypto"
3. Select assets from the dropdown
4. Click "Add Selected"
5. Repeat for each asset class (up to 35 per class)

### Step 5: Start Scheduler

1. On the Assets page, click "Start Price Updates"
2. Prices will update every 5 minutes automatically

### Step 6: View Prices

1. Click "Prices" in the navigation
2. See all your tracked assets with live price data
3. Page auto-refreshes every 10 seconds

## What You Can Test on Windows

### ✅ Web UI Features

- **Dashboard**: Overview of selected assets and scheduler status
- **Credentials**: Setup and verify Alpaca API credentials
- **Assets**: Select stocks, forex, and crypto to track
- **Prices**: View live prices with change amounts and percentages

### ✅ REST API

The REST API runs simultaneously on port 5001:

```bash
# Test from PowerShell or WSL
curl http://localhost:5001/health
curl http://localhost:5001/prices
curl http://localhost:5001/prices/stocks/AAPL
```

### ✅ Background Scheduler

- Automatic price updates every 5 minutes
- Runs in the background
- Status visible in Web UI

### ✅ Database Operations

- Credentials storage
- Asset selection
- Price history
- All CRUD operations

## Access from Other Devices

### Find Your Windows PC's IP

**PowerShell:**
```powershell
ipconfig
```

Look for "IPv4 Address" (e.g., 192.168.1.100)

**WSL:**
```bash
ip addr show eth0 | grep inet
```

### Access from Phone/Tablet

On your local network:

```
http://192.168.1.100:8080  (Web UI)
http://192.168.1.100:5001  (REST API)
```

Replace `192.168.1.100` with your actual IP.

## Testing Modes

### Mode 1: Demo Mode (No Alpaca API)

Test the interface with sample data:

```bash
./venv/bin/python demo_mode.py
```

Then open: `http://localhost:5001/prices`

This gives you sample data to test the REST API without credentials.

### Mode 2: Web UI with Real Data

Full application with web interface:

```bash
./venv/bin/python main_web.py
```

Then open: `http://localhost:8080`

Setup credentials, select assets, and get real price data.

### Mode 3: Headless Mode (API Only)

No web interface, just REST API:

```bash
./venv/bin/python main_headless.py
```

Access via: `http://localhost:5001`

## Testing Checklist

Use this checklist to ensure everything works before deploying to Pi:

- [ ] **Installation**
  - [ ] Virtual environment created
  - [ ] Dependencies installed
  - [ ] Core tests passed (`test_core.py`)

- [ ] **Web UI**
  - [ ] Application starts without errors
  - [ ] Can access http://localhost:8080
  - [ ] Dashboard loads correctly
  - [ ] Navigation works

- [ ] **Credentials**
  - [ ] Can enter Alpaca API credentials
  - [ ] Verification works
  - [ ] Credentials save to database
  - [ ] Error handling for invalid credentials

- [ ] **Asset Selection**
  - [ ] Can fetch available stocks
  - [ ] Can fetch available forex
  - [ ] Can fetch available crypto
  - [ ] Can add assets (enforces 35 limit)
  - [ ] Can remove assets
  - [ ] Selected assets persist

- [ ] **Scheduler**
  - [ ] Can start scheduler
  - [ ] Status shows "Running"
  - [ ] First update completes (wait 5 min)
  - [ ] Subsequent updates occur automatically

- [ ] **Prices**
  - [ ] Prices display correctly
  - [ ] Change amounts calculated
  - [ ] Change percentages calculated
  - [ ] Auto-refresh works
  - [ ] Filtered by class (stocks/forex/crypto)

- [ ] **REST API**
  - [ ] `/health` endpoint works
  - [ ] `/prices` endpoint works
  - [ ] `/prices/stocks` filtering works
  - [ ] `/prices/stocks/AAPL` specific asset works
  - [ ] `/status` endpoint works
  - [ ] `/assets` endpoint works

- [ ] **Network Access**
  - [ ] Can access from phone/tablet on network
  - [ ] API accessible from other devices
  - [ ] Both port 8080 and 5001 accessible

## Common Issues on Windows/WSL

### Port Already in Use

```bash
# Find and kill process using port 8080
lsof -ti:8080 | xargs kill -9

# Or use a different port in main_web.py
web_app.run(host='0.0.0.0', port=8090)
```

### Can't Access from Other Devices

**Check Windows Firewall:**

1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Create inbound rules for ports 8080 and 5001

**Or temporarily disable firewall for testing.**

### WSL Network Issues

Make sure WSL can access network:

```bash
ping google.com
```

If DNS fails, add to `/etc/wsl.conf`:

```ini
[network]
generateResolvConf = false
```

Then manually set DNS in `/etc/resolv.conf`:

```
nameserver 8.8.8.8
```

## Testing Workflow

### Complete Test Scenario

1. **Start Application**
   ```bash
   ./venv/bin/python main_web.py
   ```

2. **Open Browser**
   - Navigate to `http://localhost:8080`

3. **Setup Credentials**
   - Go to Credentials page
   - Enter Alpaca API key and secret
   - Verify they work

4. **Select Assets**
   - Go to Assets page
   - Add 5 stocks (AAPL, GOOGL, MSFT, TSLA, NVDA)
   - Add 2 crypto (BTCUSD, ETHUSD)
   - Add 2 forex (EUR/USD, GBP/USD)

5. **Start Scheduler**
   - Click "Start Price Updates"
   - Verify scheduler shows "Running" on dashboard

6. **Wait for First Update**
   - Wait ~5 minutes for first price fetch
   - Check Prices page
   - Verify all assets have price data

7. **Test REST API**
   ```bash
   curl http://localhost:5001/prices | python3 -m json.tool
   ```

8. **Test from Phone**
   - Find your PC's IP address
   - Open browser on phone
   - Navigate to `http://YOUR_IP:8080`
   - Verify everything works

9. **Verify Auto-Updates**
   - Wait another 5 minutes
   - Check that prices update automatically
   - Verify timestamps change

10. **Stop Application**
    - Press Ctrl+C in terminal
    - Verify graceful shutdown

## Performance on Windows PC

Expected performance:

- **Startup Time**: < 5 seconds
- **Web UI Load Time**: < 1 second
- **API Response Time**: < 50ms (local)
- **Price Update Time**: 2-10 seconds (depending on assets)
- **Memory Usage**: ~100MB
- **CPU Usage**: < 5% idle, < 20% during updates

## Files Generated During Testing

```
alpaca-price-hub/
├── data/
│   └── prices.db          # SQLite database (grows with price history)
├── logs/
│   └── app.log           # Application logs
└── venv/                 # Virtual environment (Windows-specific)
```

## Deployment to Raspberry Pi

Once testing is complete on Windows:

1. **Transfer Files**
   ```bash
   # From WSL
   scp -r /mnt/c/users/timot/tickertronix_complete/alpaca-price-hub pi@raspberrypi:~/
   ```

2. **On Raspberry Pi**
   ```bash
   cd ~/alpaca-price-hub
   ./install.sh
   python3 main_web.py
   ```

3. **Access from Network**
   ```
   http://raspberrypi.local:8080
   ```

The database and configuration will transfer over, so you won't need to reconfigure!

## Troubleshooting

### "Module not found" errors

```bash
# Make sure venv is activated
source venv/bin/activate  # WSL
venv\Scripts\activate     # PowerShell

# Reinstall dependencies
pip install -r requirements.txt
```

### Can't connect to Alpaca API

- Check internet connection
- Verify credentials are correct
- Check `logs/app.log` for detailed errors
- Try credentials at https://alpaca.markets first

### No prices showing

- Verify scheduler is running (Dashboard)
- Check `logs/app.log` for API errors
- Wait full 5 minutes for first update
- Ensure assets are selected (Assets page)

### Browser can't connect

- Verify application is running
- Check correct port (8080 for Web UI)
- Try `http://127.0.0.1:8080` instead of localhost
- Check Windows Firewall settings

## Next Steps

After successful Windows testing:

1. ✅ **Verified on PC** - Everything works!
2. 📦 **Transfer to Pi** - Copy tested configuration
3. 🚀 **Deploy** - Run on Raspberry Pi
4. 🌐 **Integrate** - Build apps using your local price hub!

## Support

If you encounter issues:

1. Check `logs/app.log`
2. Review this guide
3. Check `TESTING.md` for additional info
4. Verify credentials at alpaca.markets

---

**Ready to test?** Run `./venv/bin/python main_web.py` and open your browser!
