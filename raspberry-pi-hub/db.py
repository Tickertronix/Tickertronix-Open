"""
Database operations for Raspberry Pi Hub.
Uses SQLite for local storage of credentials, selected assets, and price data.
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import config

logger = logging.getLogger(__name__)


class Database:
    """Handles all database operations for the price hub."""

    def __init__(self, db_path: str = config.DB_PATH):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def init_db(self):
        """Create all necessary tables if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Config table for storing API credentials and settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Selected assets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS selected_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                asset_class TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                UNIQUE(symbol, asset_class)
            )
        """)

        # Asset prices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                asset_class TEXT NOT NULL,
                date DATE NOT NULL,
                open_price REAL,
                prev_close REAL,
                last_price REAL,
                last_updated TIMESTAMP,
                UNIQUE(symbol, asset_class, date)
            )
        """)

        # Ensure prev_close column exists (for existing databases)
        cursor.execute("PRAGMA table_info(asset_prices)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'prev_close' not in columns:
            cursor.execute("ALTER TABLE asset_prices ADD COLUMN prev_close REAL")
            logger.info("Added prev_close column to asset_prices")

        # Device registration and identification
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                device_name TEXT,
                device_type TEXT,
                device_key TEXT UNIQUE,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                enabled BOOLEAN DEFAULT 1
            )
        """)

        # Device-specific display settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_settings (
                device_id TEXT PRIMARY KEY,
                scroll_mode TEXT DEFAULT 'single',
                scroll_speed INTEGER DEFAULT 100,
                brightness INTEGER DEFAULT 10,
                update_interval INTEGER DEFAULT 300,
                top_sources TEXT DEFAULT '["stocks"]',
                bottom_sources TEXT DEFAULT '["crypto","forex"]',
                dwell_seconds INTEGER DEFAULT 3,
                asset_order TEXT DEFAULT '["stocks","crypto","forex"]',
                font TEXT DEFAULT 'default',
                updated_at TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(device_id)
            )
        """)

        # Ensure optional columns exist for upgraded databases
        cursor.execute("PRAGMA table_info(device_settings)")
        ds_cols = [row['name'] for row in cursor.fetchall()]
        if 'dwell_seconds' not in ds_cols:
            cursor.execute("ALTER TABLE device_settings ADD COLUMN dwell_seconds INTEGER DEFAULT 3")
            logger.info("Added dwell_seconds column to device_settings")
        if 'asset_order' not in ds_cols:
            cursor.execute("ALTER TABLE device_settings ADD COLUMN asset_order TEXT DEFAULT '[\"stocks\",\"crypto\",\"forex\"]'")
            logger.info("Added asset_order column to device_settings")

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    # ==================== Config Operations ====================

    def save_config(self, key: str, value: str):
        """Save or update a config value."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)
        """, (key, value))
        conn.commit()
        conn.close()
        logger.debug(f"Saved config: {key}")

    def get_config(self, key: str) -> Optional[str]:
        """Retrieve a config value."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row['value'] if row else None

    def save_credentials(self, api_key: str, api_secret: str):
        """Save Alpaca API credentials."""
        self.save_config('alpaca_api_key', api_key)
        self.save_config('alpaca_api_secret', api_secret)
        logger.info("Credentials saved successfully")

    def get_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """Retrieve stored credentials."""
        api_key = self.get_config('alpaca_api_key')
        api_secret = self.get_config('alpaca_api_secret')
        return api_key, api_secret

    # ==================== Selected Assets Operations ====================

    def add_selected_asset(self, symbol: str, asset_class: str):
        """Add an asset to the selected list."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO selected_assets (symbol, asset_class, enabled)
                VALUES (?, ?, 1)
            """, (symbol, asset_class))
            conn.commit()
            logger.info(f"Added asset: {symbol} ({asset_class})")
        except sqlite3.IntegrityError:
            # Asset already exists
            logger.warning(f"Asset already selected: {symbol} ({asset_class})")
        finally:
            conn.close()

    def remove_selected_asset(self, symbol: str, asset_class: str):
        """Remove an asset from the selected list."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM selected_assets
            WHERE symbol = ? AND asset_class = ?
        """, (symbol, asset_class))
        cursor.execute("""
            DELETE FROM asset_prices
            WHERE symbol = ? AND asset_class = ?
        """, (symbol, asset_class))
        conn.commit()
        conn.close()
        logger.info(f"Removed asset: {symbol} ({asset_class})")

    def get_selected_assets(self, asset_class: Optional[str] = None,
                            include_disabled: bool = False) -> List[Dict]:
        """Get selected assets, optionally filtered by class. Includes disabled if requested."""
        conn = self.get_connection()
        cursor = conn.cursor()

        base_query = """
            SELECT symbol, asset_class, enabled
            FROM selected_assets
        """
        params = []

        if asset_class:
            base_query += " WHERE asset_class = ?"
            params.append(asset_class)

        if not include_disabled:
            base_query += " AND enabled = 1" if asset_class else " WHERE enabled = 1"

        cursor.execute(base_query, params)

        rows = cursor.fetchall()
        conn.close()

        assets = []
        for row in rows:
            item = dict(row)
            # Normalize enabled to bool
            item['enabled'] = bool(item.get('enabled'))
            assets.append(item)

        return assets

    def count_selected_assets(self, asset_class: str) -> int:
        """Count how many assets are selected for a given class."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM selected_assets
            WHERE asset_class = ? AND enabled = 1
        """, (asset_class,))
        row = cursor.fetchone()
        conn.close()
        return row['count'] if row else 0

    def clear_selected_assets(self, asset_class: Optional[str] = None):
        """Clear all selected assets, optionally for a specific class."""
        conn = self.get_connection()
        cursor = conn.cursor()

        if asset_class:
            cursor.execute("DELETE FROM selected_assets WHERE asset_class = ?", (asset_class,))
            cursor.execute("DELETE FROM asset_prices WHERE asset_class = ?", (asset_class,))
            logger.info(f"Cleared selected assets for {asset_class}")
        else:
            cursor.execute("DELETE FROM selected_assets")
            cursor.execute("DELETE FROM asset_prices")
            logger.info("Cleared all selected assets")

        conn.commit()
        conn.close()

    def set_asset_enabled(self, symbol: str, asset_class: str, enabled: bool):
        """Enable or disable a selected asset without removing it."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE selected_assets
               SET enabled = ?
             WHERE symbol = ? AND asset_class = ?
        """, (1 if enabled else 0, symbol, asset_class))
        conn.commit()
        conn.close()

    # ==================== Price Data Operations ====================

    def update_price(self, symbol: str, asset_class: str, open_price: float,
                     last_price: float, price_date: date = None,
                     prev_close: float = None):
        """
        Update or insert price data for an asset.

        Logic:
        - If record exists for (symbol, asset_class, date): update last_price only
        - If record doesn't exist: insert with both open_price and last_price
        """
        if price_date is None:
            price_date = date.today()

        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if record exists for today
        cursor.execute("""
            SELECT id, open_price FROM asset_prices
            WHERE symbol = ? AND asset_class = ? AND date = ?
        """, (symbol, asset_class, price_date))

        existing = cursor.fetchone()
        now = datetime.now()

        if existing:
            # Update last_price and refresh open_price/prev_close if a new baseline is provided
            if (open_price is not None and open_price != existing['open_price']) or prev_close is not None:
                cursor.execute("""
                    UPDATE asset_prices
                    SET open_price = COALESCE(?, open_price),
                        prev_close = COALESCE(?, prev_close),
                        last_price = ?,
                        last_updated = ?
                    WHERE id = ?
                """, (open_price, prev_close, last_price, now, existing['id']))
                logger.debug(f"Updated price for {symbol}: open={open_price}, prev_close={prev_close}, last={last_price}")
            else:
                cursor.execute("""
                    UPDATE asset_prices
                    SET last_price = ?, last_updated = ?
                    WHERE id = ?
                """, (last_price, now, existing['id']))
                logger.debug(f"Updated price for {symbol}: last={last_price}")
        else:
            # Insert new record with both open and last price
            cursor.execute("""
                INSERT INTO asset_prices
                (symbol, asset_class, date, open_price, prev_close, last_price, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (symbol, asset_class, price_date, open_price, prev_close, last_price, now))
            logger.debug(f"Inserted new price for {symbol}: open={open_price}, prev_close={prev_close}, last={last_price}")

        conn.commit()
        conn.close()

    def get_latest_prices(self, asset_class: Optional[str] = None,
                          symbol: Optional[str] = None) -> List[Dict]:
        """
        Get the latest prices for assets.
        Can filter by asset_class and/or symbol.
        Returns calculated change_amount and change_percent.
        Only returns assets that are currently selected/enabled.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                ap.symbol,
                ap.asset_class,
                ap.date,
                ap.open_price,
                ap.prev_close,
                ap.last_price,
                ap.last_updated
            FROM asset_prices ap
            JOIN selected_assets sa
              ON ap.symbol = sa.symbol
             AND ap.asset_class = sa.asset_class
             AND sa.enabled = 1
            WHERE ap.date = (
                SELECT MAX(date)
                FROM asset_prices ap2
                WHERE ap2.symbol = ap.symbol
                AND ap2.asset_class = ap.asset_class
            )
        """

        params = []
        if asset_class:
            query += " AND ap.asset_class = ?"
            params.append(asset_class)
        if symbol:
            query += " AND ap.symbol = ?"
            params.append(symbol)

        query += " ORDER BY ap.symbol"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            price_dict = dict(row)

            # Calculate change metrics (prefer previous close like quote sites)
            prev_close = price_dict.get('prev_close')
            open_p = price_dict.get('open_price')
            last_p = price_dict.get('last_price') or 0

            baseline = prev_close if prev_close not in (None, 0) else (open_p if open_p else 0)

            if baseline and last_p:
                change_amount = last_p - baseline
                change_percent = (change_amount / baseline) * 100 if baseline != 0 else 0
            else:
                change_amount = 0
                change_percent = 0

            price_dict['change_amount'] = round(change_amount, 4)
            price_dict['change_percent'] = round(change_percent, 2)

            results.append(price_dict)

        return results

    def get_all_prices_for_date(self, price_date: date = None) -> List[Dict]:
        """Get all prices for a specific date (defaults to today)."""
        if price_date is None:
            price_date = date.today()

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM asset_prices WHERE date = ?
            ORDER BY asset_class, symbol
        """, (price_date,))

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ==================== Device Management Operations ====================

    def register_device(self, device_id: str, device_name: str,
                       device_type: str, device_key: str) -> bool:
        """Register a new device or update existing device info."""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now()
        device_type = device_type or "matrix_portal_scroll"

        try:
            cursor.execute("""
                INSERT INTO devices (device_id, device_name, device_type, device_key, first_seen, last_seen, enabled)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(device_id) DO UPDATE SET
                    device_name = excluded.device_name,
                    device_type = excluded.device_type,
                    device_key = excluded.device_key,
                    last_seen = excluded.last_seen
            """, (device_id, device_name, device_type, device_key or device_id, now, now))

            # Initialize default settings for new devices
            cursor.execute("""
                INSERT OR IGNORE INTO device_settings (device_id, updated_at)
                VALUES (?, ?)
            """, (device_id, now))

            conn.commit()
            logger.info(f"Registered device: {device_id} ({device_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to register device {device_id}: {e}")
            return False
        finally:
            conn.close()

    def get_device(self, device_id: str) -> Optional[Dict]:
        """Get device information by device_id."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_device_by_key(self, device_key: str) -> Optional[Dict]:
        """Get device information by device_key."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices WHERE device_key = ?", (device_key,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_devices(self) -> List[Dict]:
        """Get all registered devices."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices ORDER BY last_seen DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_device_last_seen(self, device_id: str):
        """Update the last_seen timestamp for a device."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE devices SET last_seen = ? WHERE device_id = ?
        """, (datetime.now(), device_id))
        conn.commit()
        conn.close()

    def enable_device(self, device_id: str, enabled: bool):
        """Enable or disable a device."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE devices SET enabled = ? WHERE device_id = ?
        """, (1 if enabled else 0, device_id))
        conn.commit()
        conn.close()
        logger.info(f"Device {device_id} {'enabled' if enabled else 'disabled'}")

    # ==================== Device Settings Operations ====================

    def get_device_settings(self, device_id: str) -> Dict:
        """Get settings for a specific device. Returns defaults if not found."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT scroll_mode, scroll_speed, brightness, update_interval,
                   top_sources, bottom_sources, dwell_seconds, asset_order, font, updated_at
            FROM device_settings
            WHERE device_id = ?
        """, (device_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            settings = dict(row)
            # Parse JSON arrays
            import json
            settings['top_sources'] = json.loads(settings.get('top_sources', '["stocks"]'))
            settings['bottom_sources'] = json.loads(settings.get('bottom_sources', '["crypto","forex"]'))
            settings['asset_order'] = json.loads(settings.get('asset_order', '["stocks","crypto","forex"]'))
            return settings
        else:
            # Return defaults
            return self.get_default_settings()

    def get_default_settings(self) -> Dict:
        """Get default device settings."""
        return {
            'scroll_mode': 'single',
            'scroll_speed': 100,
            'brightness': 10,
            'update_interval': 300,
            'top_sources': ['stocks'],
            'bottom_sources': ['crypto', 'forex'],
            'dwell_seconds': 3,
            'asset_order': ['stocks', 'crypto', 'forex'],
            'font': 'default'
        }

    def update_device_settings(self, device_id: str, settings: Dict) -> bool:
        """Update device settings. Supports partial updates."""
        import json
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now()

        try:
            # Build dynamic UPDATE query for provided settings
            set_clauses = []
            params = []

            for key, value in settings.items():
                if key in ['scroll_mode', 'scroll_speed', 'brightness', 'update_interval', 'font', 'dwell_seconds']:
                    set_clauses.append(f"{key} = ?")
                    params.append(value)
                elif key in ['top_sources', 'bottom_sources', 'asset_order']:
                    # Convert list to JSON string
                    set_clauses.append(f"{key} = ?")
                    params.append(json.dumps(value) if isinstance(value, list) else value)

            if not set_clauses:
                return False  # No valid settings to update

            set_clauses.append("updated_at = ?")
            params.append(now)
            params.append(device_id)

            query = f"UPDATE device_settings SET {', '.join(set_clauses)} WHERE device_id = ?"
            cursor.execute(query, params)

            # If no rows affected, device settings don't exist yet - insert them
            if cursor.rowcount == 0:
                # First ensure device exists
                device = self.get_device(device_id)
                if not device:
                    logger.error(f"Cannot update settings for non-existent device: {device_id}")
                    return False

                # Insert with provided settings merged with defaults
                defaults = self.get_default_settings()
                defaults.update(settings)

                cursor.execute("""
                    INSERT INTO device_settings
                    (device_id, scroll_mode, scroll_speed, brightness, update_interval,
                     top_sources, bottom_sources, dwell_seconds, asset_order, font, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    device_id,
                    defaults['scroll_mode'],
                    defaults['scroll_speed'],
                    defaults['brightness'],
                    defaults['update_interval'],
                    json.dumps(defaults['top_sources']),
                    json.dumps(defaults['bottom_sources']),
                    defaults['dwell_seconds'],
                    json.dumps(defaults['asset_order']),
                    defaults['font'],
                    now
                ))

            conn.commit()
            logger.info(f"Updated settings for device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update device settings for {device_id}: {e}")
            return False
        finally:
            conn.close()

    def touch_device_settings(self, device_id: str):
        """Update the updated_at timestamp to signal settings change."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE device_settings SET updated_at = ? WHERE device_id = ?
        """, (datetime.now(), device_id))
        conn.commit()
        conn.close()

    def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
