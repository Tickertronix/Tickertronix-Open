# Testing Guide - Alpaca Price Hub

## Overview

This guide covers testing the Alpaca Price Hub both locally (WSL/Linux) and on Raspberry Pi.

## Prerequisites

- Python 3.8+ installed
- Virtual environment activated (for local testing)
- Alpaca API credentials (get from https://alpaca.markets)

## Quick Test (No API Credentials Needed)

Test core functionality without making API calls:

```bash
# Run core tests
./venv/bin/python test_core.py
```

This validates:
- Database operations
- Module imports
- Basic functionality
- Configuration

## Full Testing (With API Credentials)

### Step 1: Setup Credentials

**Interactive Setup:**
```bash
./venv/bin/python credentials_setup.py
```

**Or via Command Line:**
```bash
./venv/bin/python main_headless.py \
  --api-key YOUR_API_KEY \
  --api-secret YOUR_API_SECRET
```

### Step 2: Select Assets

```bash
./venv/bin/python asset_selection.py
```

This provides an interactive menu to:
- View currently selected assets
- Add stocks, forex, or crypto (up to 35 each)
- Remove assets
- Clear all selections

### Step 3: Run Headless Mode

**With Scheduler (Full Operation):**
```bash
./venv/bin/python main_headless.py
```

**API Server Only (No Auto Updates):**
```bash
./venv/bin/python main_headless.py --no-scheduler
```

## Testing the API

Once the application is running, test the API endpoints:

### Health Check

```bash
curl http://localhost:5001/health
```

Expected response:
```json
{
  "status": "ok",
  "database": "ok",
  "scheduler": "running",
  "timestamp": "2024-01-01T12:00:00"
}
```

### Get All Prices

```bash
curl http://localhost:5001/prices | python3 -m json.tool
```

### Get Prices by Asset Class

```bash
# Stocks only
curl http://localhost:5001/prices/stocks | python3 -m json.tool

# Forex only
curl http://localhost:5001/prices/forex | python3 -m json.tool

# Crypto only
curl http://localhost:5001/prices/crypto | python3 -m json.tool
```

### Get Specific Asset

```bash
# Example: Apple stock
curl http://localhost:5001/prices/stocks/AAPL | python3 -m json.tool

# Example: Bitcoin
curl http://localhost:5001/prices/crypto/BTCUSD | python3 -m json.tool
```

### Get Scheduler Status

```bash
curl http://localhost:5001/status | python3 -m json.tool
```

### Get Selected Assets

```bash
# All assets
curl http://localhost:5001/assets | python3 -m json.tool

# Filter by class
curl http://localhost:5001/assets?asset_class=stocks | python3 -m json.tool
```

## Testing Workflow

### Scenario 1: Complete Local Test

```bash
# 1. Core functionality test
./venv/bin/python test_core.py

# 2. Setup credentials
./venv/bin/python credentials_setup.py
# Enter your Alpaca API credentials

# 3. Select assets
./venv/bin/python asset_selection.py
# Choose option 2 to add assets
# Add a few stocks, forex, crypto

# 4. Run the application
./venv/bin/python main_headless.py

# 5. In another terminal, test the API
curl http://localhost:5001/health
curl http://localhost:5001/prices

# 6. Wait 5 minutes for first price update, then check again
curl http://localhost:5001/prices | python3 -m json.tool

# 7. Stop with Ctrl+C
```

### Scenario 2: Quick API Test

```bash
# Start with existing credentials and selections
./venv/bin/python main_headless.py

# In another terminal
curl http://localhost:5001/status
curl http://localhost:5001/assets
curl http://localhost:5001/prices
```

### Scenario 3: Testing Without Scheduler

```bash
# Run API server only (no automatic updates)
./venv/bin/python main_headless.py --no-scheduler

# Manually trigger updates via database or wait for manual trigger
# Good for testing API functionality without price updates
```

## Testing on Raspberry Pi

### With GUI (Desktop Environment)

```bash
# Activate venv (if using one)
source venv/bin/activate

# Run full application with GUI
python3 main.py
```

### Without GUI (Headless Pi)

```bash
# Setup credentials
python3 credentials_setup.py

# Select assets
python3 asset_selection.py

# Run in background
nohup python3 main_headless.py > output.log 2>&1 &

# Check it's running
curl http://localhost:5001/health

# View logs
tail -f logs/app.log
```

## Troubleshooting Tests

### "ModuleNotFoundError"

Make sure virtual environment is activated:
```bash
source venv/bin/activate  # Linux/Mac/WSL
# or
venv\Scripts\activate     # Windows
```

### "No credentials found"

Run credentials setup:
```bash
./venv/bin/python credentials_setup.py
```

### "Port 5001 already in use"

Kill existing process:
```bash
lsof -ti:5001 | xargs kill -9
```

Or change port in `config.py`:
```python
API_PORT = 5002  # Use different port
```

### "Rate limit exceeded"

Increase `RATE_LIMIT_DELAY` in `config.py`:
```python
RATE_LIMIT_DELAY = 1.0  # Increase from 0.5 to 1.0 second
```

### GUI won't start in WSL

Install X server on Windows:
- VcXsrv: https://sourceforge.net/projects/vcxsrv/
- X410: https://x410.dev/

Set DISPLAY:
```bash
export DISPLAY=:0
python3 main.py
```

Or use headless mode:
```bash
python3 main_headless.py
```

## Validation Checklist

- [ ] Core tests pass (`test_core.py`)
- [ ] Credentials verify successfully
- [ ] Assets can be selected
- [ ] API server starts without errors
- [ ] `/health` endpoint returns "ok"
- [ ] `/prices` endpoint returns data (after first update)
- [ ] Scheduler runs automatically
- [ ] Logs are created in `logs/app.log`
- [ ] Database is created in `data/prices.db`
- [ ] Prices update every 5 minutes
- [ ] Can access API from another device on LAN (if testing networking)

## Performance Testing

### Monitor Scheduler

```bash
# Watch the logs in real-time
tail -f logs/app.log

# Check scheduler status via API
watch -n 5 'curl -s http://localhost:5001/status | python3 -m json.tool'
```

### Monitor Database Size

```bash
# Check database file size
ls -lh data/prices.db

# Query price count
sqlite3 data/prices.db "SELECT COUNT(*) FROM asset_prices;"

# View latest prices
sqlite3 data/prices.db "SELECT * FROM asset_prices ORDER BY last_updated DESC LIMIT 10;"
```

### Test Rate Limits

Add many assets (close to 35 per class) and monitor logs for any rate limit errors.

## Debugging Tips

1. **Enable Debug Logging:**
   Edit `config.py`:
   ```python
   LOG_LEVEL = 'DEBUG'
   ```

2. **Check Database:**
   ```bash
   sqlite3 data/prices.db
   .tables
   SELECT * FROM config;
   SELECT * FROM selected_assets;
   SELECT * FROM asset_prices ORDER BY last_updated DESC LIMIT 5;
   .quit
   ```

3. **Monitor Network Traffic:**
   ```bash
   # Watch API requests
   tail -f logs/app.log | grep -i "alpaca\|api"
   ```

4. **Test Individual Components:**
   ```python
   # In Python REPL
   from db import Database
   from alpaca_client import AlpacaClient

   db = Database()
   api_key, api_secret = db.get_credentials()

   client = AlpacaClient(api_key, api_secret)
   success, msg = client.verify_credentials()
   print(f"{success}: {msg}")
   ```

## Automated Testing Script

Create `run_tests.sh`:
```bash
#!/bin/bash
echo "Running Alpaca Price Hub Tests..."

# Core tests
echo "1. Core functionality..."
./venv/bin/python test_core.py || exit 1

# Check credentials
echo "2. Checking credentials..."
if ./venv/bin/python -c "from db import Database; db = Database(); k,s = db.get_credentials(); exit(0 if k and s else 1)"; then
    echo "✓ Credentials found"
else
    echo "✗ No credentials - run credentials_setup.py"
    exit 1
fi

# Start API server
echo "3. Starting API server..."
./venv/bin/python main_headless.py --no-scheduler &
PID=$!
sleep 3

# Test API
echo "4. Testing API endpoints..."
curl -s http://localhost:5001/health > /dev/null && echo "✓ /health" || echo "✗ /health"
curl -s http://localhost:5001/prices > /dev/null && echo "✓ /prices" || echo "✗ /prices"
curl -s http://localhost:5001/status > /dev/null && echo "✓ /status" || echo "✗ /status"

# Cleanup
echo "5. Cleanup..."
kill $PID

echo "Tests complete!"
```

## Next Steps After Testing

Once testing is successful:

1. **Update Configuration:**
   - Adjust `UPDATE_INTERVAL_MINUTES` if needed
   - Set appropriate `MAX_ASSETS_PER_CLASS`

2. **Setup Autostart:**
   - See README.md for systemd service setup
   - Or use cron for scheduling

3. **Production Deployment:**
   - Move to Raspberry Pi
   - Set up monitoring
   - Configure firewall rules

4. **Integration:**
   - Build apps that consume the API
   - Set up dashboards
   - Create alerts based on price changes
