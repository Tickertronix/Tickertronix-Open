#!/usr/bin/env python3
"""Test to see what crypto assets Alpaca actually provides."""

from alpaca_client import AlpacaClient
from db import Database

# Initialize
db = Database()
api_key, api_secret = db.get_credentials()
client = AlpacaClient(api_key, api_secret)

print("Fetching available crypto assets from Alpaca...")
print("-" * 60)

assets = client.get_crypto_assets()

if assets:
    print(f"Found {len(assets)} crypto assets:")
    for i, asset in enumerate(assets[:10], 1):  # Show first 10
        print(f"  {i}. Symbol: {asset['symbol']}, Name: {asset['name']}")
    if len(assets) > 10:
        print(f"  ... and {len(assets) - 10} more")
else:
    print("No crypto assets found")

# Try to get the raw data to see the actual format
print("\nTrying direct API call to see raw crypto asset data...")
import requests
url = f"{client.session.headers.get('APCA-API-KEY-ID', 'test')}"
headers = {
    'APCA-API-KEY-ID': api_key,
    'APCA-API-SECRET-KEY': api_secret
}
response = requests.get(
    "https://paper-api.alpaca.markets/v2/assets?asset_class=crypto&status=active",
    headers=headers,
    timeout=15
)
if response.status_code == 200:
    crypto_data = response.json()
    if crypto_data:
        print(f"\nFirst crypto asset (raw):")
        print(crypto_data[0])
