"""
Configuration constants for Raspberry Pi Hub application.
"""

import os

# Application paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
DB_PATH = os.path.join(DATA_DIR, 'prices.db')
LOG_PATH = os.path.join(LOG_DIR, 'app.log')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Alpaca API Configuration
ALPACA_BASE_URL = 'https://data.alpaca.markets'  # Market data endpoint
ALPACA_BROKER_URL = 'https://paper-api.alpaca.markets'  # For account verification

# Asset limits per class
MAX_ASSETS_PER_CLASS = 50

# Price update configuration
UPDATE_INTERVAL_MINUTES = 5  # How often to fetch prices

# Twelve Data (forex) budget guidance (credits are 1 per symbol)
FOREX_CREDITS_PER_DAY = 800
FOREX_CREDITS_PER_MINUTE = 8

# Twelve Data integration (forex only)
TWELVE_DATA_BASE_URL = os.environ.get('TWELVE_DATA_BASE_URL', 'https://api.twelvedata.com')
TWELVE_DATA_API_KEY = os.environ.get('TWELVE_DATA_API_KEY')
HUB_BASE_HOST = os.environ.get('HUB_BASE_HOST', 'tickertronixhub.local')
FOREX_POLL_MINUTES = 60  # dedicated forex cadence
FOREX_BATCH_SIZE = 8
FOREX_BATCH_DELAY_SEC = 10
RATE_LIMIT_DELAY = 0.5  # Delay between API calls to respect rate limits (seconds)

# Local API server configuration
API_HOST = '0.0.0.0'  # Listen on all interfaces for LAN access
API_PORT = 5001

# Logging configuration
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Asset classes
ASSET_CLASSES = {
    'stocks': 'us_equity',
    'forex': 'forex',
    'crypto': 'crypto'
}
