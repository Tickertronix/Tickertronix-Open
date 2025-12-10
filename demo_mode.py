#!/usr/bin/env python3
"""
Demo mode - runs API server with sample data (no Alpaca API needed).
Perfect for testing the API endpoints without real credentials.
"""

import sys
import logging
from datetime import datetime, date
import time
import signal

import config
from db import Database
from scheduler import PriceScheduler
from alpaca_client import AlpacaClient
from api_server import run_api_server

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sample_data(db):
    """Create sample price data for testing."""
    logger.info("Creating sample data...")

    # Sample stocks
    stocks = [
        ('AAPL', 150.00, 152.50),
        ('GOOGL', 2800.00, 2825.75),
        ('MSFT', 380.00, 378.25),
        ('TSLA', 240.00, 245.60),
        ('NVDA', 495.00, 502.30)
    ]

    # Sample crypto
    crypto = [
        ('BTCUSD', 42000.00, 42500.00),
        ('ETHUSD', 2200.00, 2215.50),
        ('SOLUSD', 95.00, 96.75)
    ]

    # Sample forex
    forex = [
        ('EUR/USD', 1.0850, 1.0865),
        ('GBP/USD', 1.2650, 1.2670)
    ]

    # Add sample stocks
    for symbol, open_price, last_price in stocks:
        db.add_selected_asset(symbol, 'stocks')
        db.update_price(symbol, 'stocks', open_price, last_price)

    # Add sample crypto
    for symbol, open_price, last_price in crypto:
        db.add_selected_asset(symbol, 'crypto')
        db.update_price(symbol, 'crypto', open_price, last_price)

    # Add sample forex
    for symbol, open_price, last_price in forex:
        db.add_selected_asset(symbol, 'forex')
        db.update_price(symbol, 'forex', open_price, last_price)

    logger.info(f"Created {len(stocks)} stocks, {len(crypto)} crypto, {len(forex)} forex")

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("Shutting down demo mode...")
    sys.exit(0)

def main():
    """Run demo mode."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 70)
    print("Alpaca Price Hub - DEMO MODE")
    print("=" * 70)
    print()
    print("Running with sample data (no Alpaca API needed)")
    print()

    # Initialize database
    db = Database(db_path='./data/demo_prices.db')

    # Create sample data
    create_sample_data(db)

    # Create dummy client and scheduler
    client = AlpacaClient()
    scheduler = PriceScheduler(db, client)

    # Start API server
    logger.info("Starting API server...")
    run_api_server(db, scheduler)

    print()
    print("=" * 70)
    print("DEMO MODE RUNNING")
    print("=" * 70)
    print(f"API Server: http://localhost:{config.API_PORT}")
    print()
    print("Try these commands in another terminal:")
    print()
    print(f"  curl http://localhost:{config.API_PORT}/health")
    print(f"  curl http://localhost:{config.API_PORT}/prices")
    print(f"  curl http://localhost:{config.API_PORT}/prices/stocks")
    print(f"  curl http://localhost:{config.API_PORT}/prices/stocks/AAPL")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Demo mode stopped")

if __name__ == '__main__':
    main()
