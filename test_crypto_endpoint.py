#!/usr/bin/env python3
"""Test different crypto price endpoints."""

import requests
from db import Database
import config

# Get credentials
db = Database()
api_key, api_secret = db.get_credentials()

headers = {
    'APCA-API-KEY-ID': api_key,
    'APCA-API-SECRET-KEY': api_secret
}

# Try different symbol formats and endpoints
test_cases = [
    ("https://data.alpaca.markets/v2/crypto/latest/bars", "BTC/USD"),
    ("https://data.alpaca.markets/v2/crypto/latest/bars", "BTCUSD"),
    ("https://data.alpaca.markets/v1beta3/crypto/us/latest/bars", "BTC/USD"),
    ("https://data.alpaca.markets/v1beta3/crypto/us/latest/bars", "BTCUSD"),
]

for url, symbol in test_cases:
    print(f"\nTrying: {url}")
    print(f"Symbol: {symbol}")
    print("-" * 60)

    try:
        response = requests.get(
            url,
            params={'symbols': symbol},
            headers=headers,
            timeout=15
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Data: {data}")
            break
        else:
            print(f"❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")
