"""
Background scheduler for periodic price updates.
Uses APScheduler to fetch prices at regular intervals.
"""

import logging
from datetime import datetime, date
from typing import Optional, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

import config
from db import Database
from alpaca_client import AlpacaClient

logger = logging.getLogger(__name__)


class PriceScheduler:
    """Manages periodic price updates for selected assets."""

    def __init__(self, db: Database, alpaca_client: AlpacaClient):
        """
        Initialize the scheduler.

        Args:
            db: Database instance
            alpaca_client: AlpacaClient instance with valid credentials
        """
        self.db = db
        self.alpaca_client = alpaca_client
        self.scheduler = BackgroundScheduler()
        self.last_update_time: Optional[datetime] = None
        self.next_update_time: Optional[datetime] = None
        self.is_running = False
        self.last_forex_update: Optional[datetime] = None

    def start(self, interval_minutes: int = config.UPDATE_INTERVAL_MINUTES):
        """
        Start the scheduler to run price updates periodically.

        Args:
            interval_minutes: How often to update prices (default from config)
        """
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        # Add the price update job
        trigger = IntervalTrigger(minutes=interval_minutes)
        self.scheduler.add_job(
            self.update_all_prices,
            trigger=trigger,
            id='price_update_job',
            name='Update all asset prices',
            replace_existing=True
        )

        # Separate forex cadence (hourly by default)
        self.scheduler.add_job(
            self.update_forex_prices,
            trigger=IntervalTrigger(minutes=getattr(config, 'FOREX_POLL_MINUTES', 60)),
            id='forex_update_job',
            name='Update forex prices (Twelve Data)',
            replace_existing=True
        )

        # Start the scheduler
        self.scheduler.start()
        self.is_running = True

        # Calculate next update time
        jobs = [j for j in self.scheduler.get_jobs() if j.id == 'price_update_job']
        if jobs:
            self.next_update_time = jobs[0].next_run_time

        logger.info(f"Scheduler started - updating every {interval_minutes} minutes")
        logger.info(f"Next update scheduled for: {self.next_update_time}")

        # Run initial update immediately
        self.scheduler.add_job(
            self.update_all_prices,
            id='initial_update',
            replace_existing=True
        )
        # Run initial forex update immediately
        self.scheduler.add_job(
            self.update_forex_prices,
            id='initial_forex_update',
            replace_existing=True
        )

    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return

        self.scheduler.shutdown(wait=False)
        self.is_running = False
        logger.info("Scheduler stopped")

    def update_all_prices(self):
        """
        Main function to update prices for all selected assets.
        This is called periodically by the scheduler.
        """
        logger.info("=" * 60)
        logger.info("Starting scheduled price update")
        logger.info("=" * 60)

        update_start = datetime.now()

        try:
            # Get all selected assets grouped by class
            all_assets = self.db.get_selected_assets()

            if not all_assets:
                logger.warning("No assets selected for tracking")
                return

            # Group assets by class
            assets_by_class = {
                'stocks': [],
                'forex': [],
                'crypto': []
            }

            for asset in all_assets:
                asset_class = asset['asset_class']
                if asset_class in assets_by_class:
                    assets_by_class[asset_class].append(asset['symbol'])

            # Update prices for each asset class
            total_updated = 0

            for asset_class, symbols in assets_by_class.items():
                if not symbols:
                    continue
                # Skip forex here; handled by dedicated job to respect Twelve Data limits
                if asset_class == 'forex':
                    continue

                logger.info(f"Updating {len(symbols)} {asset_class} assets...")
                updated = self._update_class_prices(asset_class, symbols)
                total_updated += updated

            # Update timestamps
            self.last_update_time = update_start
            jobs = self.scheduler.get_jobs()
            if jobs:
                self.next_update_time = jobs[0].next_run_time

            update_duration = (datetime.now() - update_start).total_seconds()
            logger.info(f"Price update completed: {total_updated} assets updated in {update_duration:.2f}s")
            logger.info(f"Next update: {self.next_update_time}")

        except Exception as e:
            logger.error(f"Error during price update: {e}", exc_info=True)

    def update_forex_prices(self):
        """
        Dedicated forex updater (uses Twelve Data via scheduler).
        """
        try:
            assets = self.db.get_selected_assets(asset_class='forex')
            # Only enabled ones
            symbols = [a['symbol'] for a in assets if a.get('enabled')]
            if not symbols:
                logger.info("No forex assets selected/enabled; skipping forex update")
                return

            updated = self._update_class_prices('forex', symbols, use_twelve_data=True)
            self.last_forex_update = datetime.now()
            logger.info(f"Forex update completed: {updated} assets updated")
        except Exception as e:
            logger.error(f"Error during forex update: {e}", exc_info=True)

    def _update_class_prices(self, asset_class: str, symbols: List[str], use_twelve_data: bool = False) -> int:
        """
        Update prices for a specific asset class.

        Args:
            asset_class: 'stocks', 'forex', or 'crypto'
            symbols: List of symbols to update
            use_twelve_data: If True, fetch forex from Twelve Data client

        Returns:
            Number of assets successfully updated
        """
        try:
            # Fetch latest prices from Alpaca
            if use_twelve_data and asset_class == 'forex':
                try:
                    from twelvedata_client import TwelveDataClient
                    td_client = TwelveDataClient()
                    prices = td_client.get_forex_quotes(symbols)
                except Exception as e:
                    logger.error(f"Twelve Data client error: {e}", exc_info=True)
                    prices = {}
            else:
                prices = self.alpaca_client.get_prices_for_class(asset_class, symbols)

            if not prices:
                logger.warning(f"No prices received for {asset_class}")
                return 0

            # Update database
            updated_count = 0
            today = date.today()

            for symbol, price_data in prices.items():
                try:
                    open_price = price_data.get('open')
                    last_price = price_data.get('last')
                    prev_close = price_data.get('prev_close')

                    if open_price is not None and last_price is not None:
                        self.db.update_price(
                            symbol=symbol,
                            asset_class=asset_class,
                            open_price=open_price,
                            last_price=last_price,
                            price_date=today,
                            prev_close=prev_close
                        )
                        updated_count += 1
                        logger.debug(f"{symbol}: open={open_price}, last={last_price}")
                    else:
                        logger.warning(f"Missing price data for {symbol}")

                except Exception as e:
                    logger.error(f"Error updating {symbol}: {e}")
                    continue

            logger.info(f"Updated {updated_count}/{len(symbols)} {asset_class} prices")
            return updated_count

        except Exception as e:
            logger.error(f"Error updating {asset_class} prices: {e}")
            return 0

    def get_status(self) -> dict:
        """
        Get current scheduler status.

        Returns:
            Dict with status information
        """
        return {
            'is_running': self.is_running,
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None,
            'next_update': self.next_update_time.isoformat() if self.next_update_time else None,
            'interval_minutes': config.UPDATE_INTERVAL_MINUTES,
            'forex_interval_minutes': getattr(config, 'FOREX_POLL_MINUTES', None),
            'last_forex_update': self.last_forex_update.isoformat() if self.last_forex_update else None
        }

    def trigger_manual_update(self):
        """Trigger an immediate price update outside the schedule."""
        if not self.is_running:
            logger.warning("Cannot trigger update - scheduler not running")
            return

        logger.info("Triggering manual price update")
        self.scheduler.add_job(
            self.update_all_prices,
            id='manual_update',
            replace_existing=True
        )
