#!/usr/bin/env python3
"""
Interactive credentials setup for Alpaca Price Hub.
Stores credentials in the database for use by the application.
"""

import sys
import getpass
from db import Database
from alpaca_client import AlpacaClient

print("=" * 70)
print("Alpaca Price Hub - Credentials Setup")
print("=" * 70)
print()
print("This script will save your Alpaca API credentials to the database.")
print("You can get your credentials from: https://alpaca.markets")
print()

# Initialize database
print("Initializing database...")
db = Database()

# Check for existing credentials
existing_key, existing_secret = db.get_credentials()
if existing_key:
    print(f"\nExisting credentials found:")
    print(f"  API Key: {existing_key[:10]}...")
    print()
    overwrite = input("Overwrite existing credentials? (y/n): ").lower()
    if overwrite != 'y':
        print("Cancelled.")
        sys.exit(0)

print()
print("Enter your Alpaca API credentials:")
print()

# Get API Key
api_key = input("API Key ID: ").strip()
if not api_key:
    print("Error: API Key cannot be empty")
    sys.exit(1)

# Get API Secret (hidden input)
api_secret = getpass.getpass("API Secret Key: ").strip()
if not api_secret:
    print("Error: API Secret cannot be empty")
    sys.exit(1)

print()
print("Verifying credentials...")

# Verify with Alpaca
client = AlpacaClient(api_key, api_secret)
success, message = client.verify_credentials()

if not success:
    print(f"\n✗ Verification failed: {message}")
    print("\nPlease check your credentials and try again.")
    sys.exit(1)

print(f"✓ {message}")
print()

# Save to database
db.save_credentials(api_key, api_secret)
print("✓ Credentials saved to database")

print()
print("=" * 70)
print("Setup complete!")
print("=" * 70)
print()
print("You can now run the application:")
print("  - GUI mode: python3 main.py")
print("  - Headless mode: python3 main_headless.py")
print()
