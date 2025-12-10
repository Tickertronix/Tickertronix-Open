#!/usr/bin/env python3
"""Quick test to verify crypto price fetching fix."""

from alpaca_client import AlpacaClient
from db import Database

# Initialize
db = Database()
api_key, api_secret = db.get_credentials()
client = AlpacaClient(api_key, api_secret)

# Test with crypto symbols that have slashes
test_symbols = ['BTC/USD', 'ETH/USD', 'DOGE/USD']

print(f"Testing crypto price fetch with symbols: {test_symbols}")
print("-" * 60)

result = client.get_latest_crypto_prices(test_symbols)

if result:
    print(f"✅ Success! Fetched {len(result)} crypto prices:")
    for symbol, data in result.items():
        print(f"  {symbol}: ${data.get('last', 0):,.2f}")
else:
    print("❌ Failed to fetch crypto prices")
