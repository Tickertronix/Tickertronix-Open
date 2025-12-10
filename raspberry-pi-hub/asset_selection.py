#!/usr/bin/env python3
"""
Interactive asset selection for Raspberry Pi Hub.
Command-line tool to select assets when GUI is not available.
"""

import sys
from db import Database
from alpaca_client import AlpacaClient
import config

def display_menu():
    """Display main menu."""
    print("\n" + "=" * 70)
    print("Asset Selection Menu")
    print("=" * 70)
    print("1. View currently selected assets")
    print("2. Add assets")
    print("3. Remove assets")
    print("4. Clear all selections")
    print("5. Exit")
    print("=" * 70)

def view_selected(db):
    """Display currently selected assets."""
    print("\n" + "-" * 70)
    print("Currently Selected Assets")
    print("-" * 70)

    for asset_class in ['stocks', 'forex', 'crypto']:
        assets = db.get_selected_assets(asset_class)
        count = len(assets)
        print(f"\n{asset_class.upper()}: {count}/{config.MAX_ASSETS_PER_CLASS}")
        if assets:
            symbols = [a['symbol'] for a in assets]
            # Print in columns
            for i in range(0, len(symbols), 5):
                print("  " + ", ".join(symbols[i:i+5]))
        else:
            print("  (none)")

def add_assets(db, client):
    """Add assets interactively."""
    print("\n" + "-" * 70)
    print("Add Assets")
    print("-" * 70)
    print("1. Stocks")
    print("2. Forex")
    print("3. Crypto")
    print("4. Back")

    choice = input("\nSelect asset class: ").strip()

    asset_class_map = {
        '1': ('stocks', 'Stocks'),
        '2': ('forex', 'Forex'),
        '3': ('crypto', 'Crypto')
    }

    if choice not in asset_class_map:
        return

    asset_class, display_name = asset_class_map[choice]

    # Check current count
    current_count = db.count_selected_assets(asset_class)
    remaining = config.MAX_ASSETS_PER_CLASS - current_count

    if remaining <= 0:
        print(f"\n✗ Maximum assets ({config.MAX_ASSETS_PER_CLASS}) already selected for {display_name}")
        return

    print(f"\nYou can add {remaining} more {display_name.lower()}")
    print("\nFetching available assets from Alpaca...")

    # Fetch available assets
    if asset_class == 'stocks':
        assets = client.get_stock_assets()
    elif asset_class == 'forex':
        assets = client.get_forex_assets()
    else:
        assets = client.get_crypto_assets()

    if not assets:
        print("✗ Failed to fetch assets from Alpaca")
        return

    print(f"\nFound {len(assets)} available {display_name.lower()}")
    print("\nEnter symbols to add (comma-separated):")
    print("Examples: AAPL,GOOGL,MSFT  or  BTCUSD,ETHUSD")
    print()

    symbols_input = input("Symbols: ").strip().upper()
    if not symbols_input:
        return

    symbols = [s.strip() for s in symbols_input.split(',')]

    # Validate and add
    added = 0
    for symbol in symbols:
        if added >= remaining:
            print(f"\n✗ Limit reached ({config.MAX_ASSETS_PER_CLASS} max)")
            break

        # Check if symbol exists in available assets
        symbol_exists = any(a['symbol'] == symbol for a in assets)
        if not symbol_exists:
            print(f"✗ {symbol} not found in available {display_name.lower()}")
            continue

        try:
            db.add_selected_asset(symbol, asset_class)
            print(f"✓ Added {symbol}")
            added += 1
        except Exception as e:
            print(f"✗ Failed to add {symbol}: {e}")

    print(f"\nAdded {added} assets")

def remove_assets(db):
    """Remove assets interactively."""
    print("\n" + "-" * 70)
    print("Remove Assets")
    print("-" * 70)
    print("1. Stocks")
    print("2. Forex")
    print("3. Crypto")
    print("4. Back")

    choice = input("\nSelect asset class: ").strip()

    asset_class_map = {
        '1': ('stocks', 'Stocks'),
        '2': ('forex', 'Forex'),
        '3': ('crypto', 'Crypto')
    }

    if choice not in asset_class_map:
        return

    asset_class, display_name = asset_class_map[choice]

    # Get current selections
    assets = db.get_selected_assets(asset_class)
    if not assets:
        print(f"\n✗ No {display_name.lower()} currently selected")
        return

    symbols = [a['symbol'] for a in assets]
    print(f"\nCurrently selected {display_name.lower()}:")
    for i, symbol in enumerate(symbols, 1):
        print(f"  {i}. {symbol}")

    print("\nEnter symbols to remove (comma-separated):")
    symbols_input = input("Symbols: ").strip().upper()
    if not symbols_input:
        return

    to_remove = [s.strip() for s in symbols_input.split(',')]

    removed = 0
    for symbol in to_remove:
        if symbol in symbols:
            try:
                db.remove_selected_asset(symbol, asset_class)
                print(f"✓ Removed {symbol}")
                removed += 1
            except Exception as e:
                print(f"✗ Failed to remove {symbol}: {e}")
        else:
            print(f"✗ {symbol} not in selected list")

    print(f"\nRemoved {removed} assets")

def clear_all(db):
    """Clear all selected assets."""
    print("\n" + "-" * 70)
    confirm = input("Clear ALL selected assets? This cannot be undone. (yes/no): ")
    if confirm.lower() == 'yes':
        db.clear_selected_assets()
        print("✓ All selections cleared")
    else:
        print("Cancelled")

def main():
    """Main entry point."""
    print("=" * 70)
    print("Raspberry Pi Hub - Asset Selection")
    print("=" * 70)

    # Initialize database
    print("\nInitializing database...")
    db = Database()

    # Load credentials
    api_key, api_secret = db.get_credentials()
    if not api_key or not api_secret:
        print("\n✗ No credentials found in database")
        print("\nPlease run credentials_setup.py first:")
        print("  python3 credentials_setup.py")
        sys.exit(1)

    # Initialize Alpaca client
    print("Initializing Alpaca client...")
    client = AlpacaClient(api_key, api_secret)

    # Verify credentials
    success, message = client.verify_credentials()
    if not success:
        print(f"\n✗ Credential verification failed: {message}")
        sys.exit(1)

    print(f"✓ {message}")

    # Main loop
    while True:
        display_menu()
        choice = input("\nSelect option: ").strip()

        if choice == '1':
            view_selected(db)
        elif choice == '2':
            add_assets(db, client)
        elif choice == '3':
            remove_assets(db)
        elif choice == '4':
            clear_all(db)
        elif choice == '5':
            print("\nExiting...")
            break
        else:
            print("\n✗ Invalid option")

    print("\n" + "=" * 70)
    print("Asset selection complete!")
    print("=" * 70)
    print("\nYou can now start the price hub:")
    print("  python3 main_headless.py")
    print()

if __name__ == '__main__':
    main()
