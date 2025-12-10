#!/usr/bin/env python3
"""
Test script for core functionality without GUI.
Tests database, API client, and scheduler components.
"""

import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 70)
print("Raspberry Pi Hub - Core Functionality Test")
print("=" * 70)
print()

# Test 1: Database
print("TEST 1: Database Initialization")
print("-" * 70)
try:
    from db import Database
    db = Database(db_path='./data/test_prices.db')
    print("✓ Database initialized successfully")

    # Test config operations
    db.save_config('test_key', 'test_value')
    value = db.get_config('test_key')
    assert value == 'test_value', "Config save/get failed"
    print("✓ Config operations working")

    # Test asset operations
    db.add_selected_asset('AAPL', 'stocks')
    db.add_selected_asset('BTCUSD', 'crypto')
    assets = db.get_selected_assets()
    assert len(assets) == 2, "Asset operations failed"
    print("✓ Asset selection working")

    # Test price operations
    db.update_price('AAPL', 'stocks', open_price=150.0, last_price=152.5)
    prices = db.get_latest_prices()
    assert len(prices) >= 1, "Price operations failed"
    print(f"✓ Price storage working - stored {len(prices)} prices")

    # Health check
    assert db.health_check(), "Health check failed"
    print("✓ Database health check passed")

    print("\n✓ DATABASE TEST PASSED\n")
except Exception as e:
    print(f"\n✗ DATABASE TEST FAILED: {e}\n")
    sys.exit(1)

# Test 2: Alpaca Client (without actual API calls)
print("TEST 2: Alpaca Client Initialization")
print("-" * 70)
try:
    from alpaca_client import AlpacaClient

    # Initialize without credentials
    client = AlpacaClient()
    print("✓ Alpaca client initialized")

    # Set dummy credentials (won't actually verify)
    client.set_credentials('dummy_key', 'dummy_secret')
    print("✓ Credentials can be set")

    # Note: We won't actually call the API to avoid needing real credentials
    print("✓ Client methods available (not testing API calls)")

    print("\n✓ ALPACA CLIENT TEST PASSED\n")
except Exception as e:
    print(f"\n✗ ALPACA CLIENT TEST FAILED: {e}\n")
    sys.exit(1)

# Test 3: Scheduler (without starting it)
print("TEST 3: Scheduler Initialization")
print("-" * 70)
try:
    from scheduler import PriceScheduler

    # Create scheduler instance
    scheduler = PriceScheduler(db, client)
    print("✓ Scheduler initialized")

    # Check status (should not be running)
    status = scheduler.get_status()
    assert status['is_running'] == False, "Scheduler shouldn't be running yet"
    print("✓ Scheduler status check working")

    print("\n✓ SCHEDULER TEST PASSED\n")
except Exception as e:
    print(f"\n✗ SCHEDULER TEST FAILED: {e}\n")
    sys.exit(1)

# Test 4: API Server (without starting it)
print("TEST 4: API Server Initialization")
print("-" * 70)
try:
    from api_server import init_api

    # Initialize API with db and scheduler
    init_api(db, scheduler)
    print("✓ API initialized with database and scheduler")

    print("\n✓ API SERVER TEST PASSED\n")
except Exception as e:
    print(f"\n✗ API SERVER TEST FAILED: {e}\n")
    sys.exit(1)

# Test 5: Configuration
print("TEST 5: Configuration Module")
print("-" * 70)
try:
    import config

    print(f"✓ Database path: {config.DB_PATH}")
    print(f"✓ API host: {config.API_HOST}")
    print(f"✓ API port: {config.API_PORT}")
    print(f"✓ Update interval: {config.UPDATE_INTERVAL_MINUTES} minutes")
    print(f"✓ Max assets per class: {config.MAX_ASSETS_PER_CLASS}")

    print("\n✓ CONFIGURATION TEST PASSED\n")
except Exception as e:
    print(f"\n✗ CONFIGURATION TEST FAILED: {e}\n")
    sys.exit(1)

# Summary
print("=" * 70)
print("ALL CORE TESTS PASSED!")
print("=" * 70)
print()
print("The core functionality is working correctly.")
print()
print("Next steps for full testing:")
print("1. Get Alpaca API credentials from https://alpaca.markets")
print("2. Run the full application with: python3 main.py")
print("3. Or test API client with real credentials using test_api.py")
print()
print("For WSL GUI testing, you'll need:")
print("- Install X server on Windows (e.g., VcXsrv, X410)")
print("- Set DISPLAY environment variable")
print("- Or use the API-only mode (coming next)")
print()
