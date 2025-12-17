"""
Alpaca Market Data API client.
Handles all interactions with Alpaca's free-tier market data endpoints.
"""

import requests
import logging
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import config

logger = logging.getLogger(__name__)


class AlpacaClient:
    """Client for Alpaca Market Data API (free tier, data-only)."""

    def __init__(self, api_key: str = None, api_secret: str = None):
        """
        Initialize Alpaca client with credentials.

        Args:
            api_key: Alpaca API Key ID
            api_secret: Alpaca API Secret Key
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()

        # Set up authentication headers
        if api_key and api_secret:
            self.session.headers.update({
                'APCA-API-KEY-ID': api_key,
                'APCA-API-SECRET-KEY': api_secret
            })

    @staticmethod
    def _parse_iso_ts(ts: Optional[str]) -> Optional[datetime]:
        """Parse an ISO-8601 timestamp into a datetime object."""
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except Exception:
            return None

    def set_credentials(self, api_key: str, api_secret: str):
        """Update credentials after initialization."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.session.headers.update({
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': api_secret
        })

    def verify_credentials(self) -> Tuple[bool, str]:
        """
        Verify that credentials are valid by making a test API call.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Use the account endpoint for verification
            url = f"{config.ALPACA_BROKER_URL}/v2/account"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                logger.info("Credentials verified successfully")
                return True, "Credentials verified successfully"
            elif response.status_code == 401:
                logger.warning("Invalid credentials")
                return False, "Invalid credentials - please check your API key and secret"
            else:
                logger.error(f"Verification failed with status {response.status_code}")
                return False, f"Verification failed: {response.text}"

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during verification: {e}")
            return False, f"Network error: {str(e)}"

    def get_available_assets(self, asset_class: str) -> List[Dict]:
        """
        Fetch available assets from Alpaca for a given class.

        Args:
            asset_class: One of 'us_equity', 'crypto', 'forex'

        Returns:
            List of asset dictionaries with 'symbol', 'name', 'class'
        """
        try:
            url = f"{config.ALPACA_BROKER_URL}/v2/assets"
            params = {'asset_class': asset_class, 'status': 'active'}

            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()

            assets = response.json()
            logger.info(f"Fetched {len(assets)} {asset_class} assets")

            # For crypto, filter to tradable ones
            if asset_class == 'crypto':
                assets = [a for a in assets if a.get('tradable', False)]

            return assets

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {asset_class} assets: {e}")
            return []

    def get_stock_assets(self) -> List[Dict]:
        """Get available stock symbols."""
        assets = self.get_available_assets('us_equity')
        # Filter to common stocks only (exclude options, etc.)
        stocks = [
            {'symbol': a['symbol'], 'name': a.get('name', a['symbol'])}
            for a in assets
            if a.get('tradable', False) and a.get('easy_to_borrow', True)
        ]
        return sorted(stocks, key=lambda x: x['symbol'])

    def get_forex_assets(self) -> List[Dict]:
        """
        Get available forex pairs from Alpaca API.
        Falls back to hardcoded list if API fetch fails.
        """
        try:
            # Try to fetch from Alpaca's assets endpoint
            logger.info("Fetching forex pairs from Alpaca API...")
            assets = self.get_available_assets('fx')  # Try 'fx' class

            if assets:
                # Successfully fetched from API
                forex_pairs = []
                for asset in assets:
                    symbol = asset.get('symbol', '')
                    # Alpaca forex symbols might be like 'EURUSD' or 'EUR/USD'
                    # Normalize to 'EUR/USD' format
                    if '/' not in symbol and len(symbol) == 6:
                        # Convert EURUSD to EUR/USD
                        formatted = f"{symbol[:3]}/{symbol[3:]}"
                    else:
                        formatted = symbol

                    forex_pairs.append({
                        'symbol': formatted,
                        'name': formatted
                    })

                if forex_pairs:
                    logger.info(f"Fetched {len(forex_pairs)} forex pairs from API")
                    return sorted(forex_pairs, key=lambda x: x['symbol'])

        except Exception as e:
            logger.warning(f"Could not fetch forex from API: {e}, using fallback list")

        # Fallback to comprehensive hardcoded list
        logger.info("Using hardcoded forex pairs list")
        forex_pairs = [
            # Major pairs
            'EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF',
            'AUD/USD', 'USD/CAD', 'NZD/USD',

            # Minor crosses (EUR crosses)
            'EUR/GBP', 'EUR/JPY', 'EUR/CHF', 'EUR/AUD',
            'EUR/CAD', 'EUR/NZD',

            # Minor crosses (GBP crosses)
            'GBP/JPY', 'GBP/CHF', 'GBP/AUD', 'GBP/CAD',
            'GBP/NZD',

            # Minor crosses (JPY crosses)
            'AUD/JPY', 'CAD/JPY', 'CHF/JPY', 'NZD/JPY',

            # Minor crosses (AUD crosses)
            'AUD/CAD', 'AUD/CHF', 'AUD/NZD',

            # Minor crosses (other)
            'CAD/CHF', 'NZD/CAD', 'NZD/CHF',

            # Exotic pairs
            'USD/MXN', 'USD/ZAR', 'USD/TRY', 'USD/SGD',
            'USD/HKD', 'USD/NOK', 'USD/SEK', 'USD/DKK',
            'EUR/NOK', 'EUR/SEK', 'EUR/DKK', 'EUR/TRY',
            'GBP/NOK', 'GBP/SEK', 'USD/CNH', 'USD/PLN',
            'EUR/PLN', 'USD/HUF', 'EUR/HUF', 'USD/CZK', 'EUR/CZK'
        ]

        return [{'symbol': pair, 'name': pair} for pair in sorted(forex_pairs)]

    def get_crypto_assets(self) -> List[Dict]:
        """Get available cryptocurrency symbols."""
        assets = self.get_available_assets('crypto')
        cryptos = [
            {'symbol': a['symbol'], 'name': a.get('name', a['symbol'])}
            for a in assets
        ]
        return sorted(cryptos, key=lambda x: x['symbol'])

    def _fetch_stock_snapshots(self, symbols: List[str], feed: str = 'iex') -> Dict[str, Dict]:
        """
        Fetch stock snapshots for a given feed (iex or delayed_sip).

        Args:
            symbols: List of stock symbols
            feed: Alpaca feed name ('iex' or 'delayed_sip')

        Returns:
            Dict mapping symbol to snapshot sections
        """
        if not symbols:
            return {}

        snapshots_url = f"{config.ALPACA_BASE_URL}/v2/stocks/snapshots"
        try:
            response = self.session.get(
                snapshots_url,
                params={'symbols': ','.join(symbols), 'feed': feed},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Stock snapshots request failed for feed {feed}: {e}")
            return {}

        raw_snapshots = data.get('snapshots') if isinstance(data, dict) else None
        if raw_snapshots is None and isinstance(data, dict):
            # Some responses may just be the symbol map
            raw_snapshots = data

        if not isinstance(raw_snapshots, dict):
            logger.warning("Unexpected snapshots payload shape")
            return {}

        snapshots = {}
        for symbol in symbols:
            snap = raw_snapshots.get(symbol)
            if not isinstance(snap, dict):
                continue
            snapshots[symbol] = {
                'latest_trade': snap.get('latestTrade') or {},
                'latest_quote': snap.get('latestQuote') or {},
                'minute_bar': snap.get('minuteBar') or {},
                'daily_bar': snap.get('dailyBar') or {},
                'prev_daily': snap.get('prevDailyBar') or {}
            }

        return snapshots

    def _build_stock_price_from_snapshots(self, symbol: str,
                                          live_snapshot: Optional[Dict],
                                          baseline_snapshot: Optional[Dict]) -> Optional[Dict]:
        """
        Merge live (IEX) and baseline (delayed SIP) snapshots into one price record.
        """
        if not live_snapshot and not baseline_snapshot:
            return None

        live = live_snapshot or {}
        baseline = baseline_snapshot or live
        today = datetime.utcnow().date()

        latest_trade = live.get('latest_trade', {}) or {}
        latest_quote = live.get('latest_quote', {}) or {}
        minute_bar = live.get('minute_bar', {}) or {}
        daily_bar = baseline.get('daily_bar', {}) or live.get('daily_bar', {})
        prev_daily = baseline.get('prev_daily', {}) or live.get('prev_daily', {})

        bid = latest_quote.get('bp') or 0
        ask = latest_quote.get('ap') or 0
        mid = (bid + ask) / 2 if bid and ask else (ask or bid or 0)

        trade_ts = self._parse_iso_ts(latest_trade.get('t'))
        last = latest_trade.get('p') or minute_bar.get('c') or (daily_bar.get('c') if daily_bar else None) or mid
        if trade_ts and trade_ts.date() != today and minute_bar:
            # Trade is stale (after hours/weekend); prefer the minute bar close
            last = minute_bar.get('c') or last

        open_price = None
        if daily_bar:
            open_price = daily_bar.get('o')
        if open_price is None and minute_bar:
            open_price = minute_bar.get('o')
        if open_price is None and prev_daily:
            open_price = prev_daily.get('o')

        prev_close = prev_daily.get('c') if prev_daily else None
        if prev_close is None and daily_bar:
            prev_close = daily_bar.get('o')

        timestamp = latest_trade.get('t') or latest_quote.get('t') or minute_bar.get('t') or (daily_bar.get('t') if daily_bar else None)

        if last is None:
            return None

        if prev_close is None:
            prev_close = open_price if open_price is not None else last
        if open_price is None:
            open_price = prev_close if prev_close is not None else last

        return {
            'open': open_price,
            'prev_close': prev_close,
            'last': last,
            'bid': bid,
            'ask': ask,
            'timestamp': timestamp
        }

    def get_latest_stock_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch latest price data for stocks using latest quotes (IEX feed).

        Args:
            symbols: List of stock symbols

        Returns:
            Dict mapping symbol to price data:
            {
                'AAPL': {'open': 150.0, 'last': 152.5, 'timestamp': '2024-01-01T12:00:00Z'},
                ...
            }
        """
        if not symbols:
            return {}

        # Normalize symbols
        symbols = [s.upper() for s in symbols]

        results = {}

        # Snapshots: live IEX for current pricing, delayed_sip for authoritative daily/prev bars
        live_snapshots = self._fetch_stock_snapshots(symbols, feed='iex')
        baseline_snapshots = self._fetch_stock_snapshots(symbols, feed='delayed_sip')

        for symbol in symbols:
            price = self._build_stock_price_from_snapshots(
                symbol,
                live_snapshots.get(symbol),
                baseline_snapshots.get(symbol)
            )
            if price:
                results[symbol] = price

        symbols_to_fetch = [s for s in symbols if s not in results]
        if not symbols_to_fetch:
            logger.info(f"Fetched prices for {len(results)} stocks via snapshots (iex + delayed_sip)")
            return results

        latest_quotes_url = f"{config.ALPACA_BASE_URL}/v2/stocks/quotes/latest"
        daily_bars_url = f"{config.ALPACA_BASE_URL}/v2/stocks/bars"
        daily_start = (datetime.utcnow() - timedelta(days=10)).isoformat() + "Z"

        try:
            # Daily bars to derive today's open and previous close
            daily_resp = self.session.get(
                daily_bars_url,
                params={
                    'symbols': ','.join(symbols_to_fetch),
                    'timeframe': '1Day',
                    'start': daily_start,
                    'limit': 5,
                    'feed': 'iex'
                },
                timeout=15
            )
            daily_resp.raise_for_status()
            daily_data = daily_resp.json().get('bars', {})

            # Organize daily bars
            daily_info = {}
            for symbol, bars in daily_data.items():
                if bars:
                    sorted_bars = sorted(bars, key=lambda b: b.get('t'))
                    current_day = sorted_bars[-1]
                    prev_day = sorted_bars[-2] if len(sorted_bars) > 1 else None
                    daily_info[symbol] = {'current': current_day, 'previous': prev_day}

            # Latest quotes for live pricing
            quotes_resp = self.session.get(
                latest_quotes_url,
                params={'symbols': ','.join(symbols_to_fetch), 'feed': 'iex'},
                timeout=15
            )
            quotes_resp.raise_for_status()
            latest_quotes = quotes_resp.json().get('quotes', {})

            today = datetime.utcnow().date()

            for symbol in symbols_to_fetch:
                daily_bar_info = daily_info.get(symbol, {})
                current_day_bar = daily_bar_info.get('current')
                prev_day_bar = daily_bar_info.get('previous')
                quote = latest_quotes.get(symbol)

                # Baseline values
                open_price = current_day_bar.get('o') if current_day_bar else None
                prev_close = prev_day_bar.get('c') if prev_day_bar else None
                if prev_close is None and current_day_bar:
                    prev_close = current_day_bar.get('c')

                last = None
                bid = ask = 0

                quote_ts = None
                if quote and quote.get('t'):
                    try:
                        quote_ts = datetime.fromisoformat(quote['t'].replace('Z', '+00:00'))
                    except Exception:
                        quote_ts = None

                if quote:
                    bid = quote.get('bp') or 0
                    ask = quote.get('ap') or 0
                    mid = (bid + ask) / 2 if bid and ask else (ask or bid or 0)
                    # Use live mid only if quote is from today; otherwise fall back to daily close
                    if quote_ts and quote_ts.date() == today:
                        last = mid
                    elif current_day_bar:
                        last = current_day_bar.get('c')
                    else:
                        last = mid
                if last is None and current_day_bar:
                    last = current_day_bar.get('c')

                if prev_close is None:
                    prev_close = open_price if open_price is not None else last
                if open_price is None:
                    open_price = prev_close if prev_close is not None else last

                if last is not None:
                    results[symbol] = {
                        'open': open_price,
                        'prev_close': prev_close,
                        'last': last,
                        'bid': bid,
                        'ask': ask,
                        'timestamp': quote.get('t') if quote else (current_day_bar.get('t') if current_day_bar else None)
                    }

            logger.info(f"Fetched prices for {len(results)} stocks")
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching stock prices: {e}")
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                logger.warning("Rate limit hit - backing off")
            return {}

    def get_latest_crypto_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch latest cryptocurrency prices.

        Args:
            symbols: List of crypto symbols (e.g., ['BTC/USD', 'ETH/USD'])

        Returns:
            Dict mapping symbol to price data
        """
        if not symbols:
            return {}

        # Normalize symbols to uppercase to match Alpaca expectations
        symbols = [s.upper() for s in symbols]

        bars_url = f"{config.ALPACA_BASE_URL}/v1beta3/crypto/us/latest/bars"
        daily_bars_url = f"{config.ALPACA_BASE_URL}/v1beta3/crypto/us/bars"
        quotes_url = f"{config.ALPACA_BASE_URL}/v1beta3/crypto/us/latest/quotes"
        daily_start = (datetime.utcnow() - timedelta(days=10)).isoformat() + "Z"
        params = {'symbols': ','.join(symbols)}
        today = datetime.utcnow().date()

        try:
            # Fetch daily bars to get today's open and previous close
            daily_bars = {}
            try:
                daily_resp = self.session.get(
                    daily_bars_url,
                    params={
                        'symbols': ','.join(symbols),
                        'timeframe': '1Day',
                        'start': daily_start,
                        'limit': 5  # grab several sessions to cover weekends
                    },
                    timeout=15
                )
                daily_resp.raise_for_status()
                daily_data = daily_resp.json().get('bars', {})
                for symbol, bar_list in daily_data.items():
                    if bar_list:
                        sorted_bars = sorted(bar_list, key=lambda b: b.get('t'))
                        current_bar = sorted_bars[-1]
                        prev_bar = sorted_bars[-2] if len(sorted_bars) > 1 else None
                    daily_bars[symbol] = {'current': current_bar, 'previous': prev_bar}
            except requests.exceptions.RequestException as daily_err:
                logger.warning(f"Error fetching daily crypto bars: {daily_err}")

            # Latest quotes for live price
            quotes = {}
            try:
                quote_resp = self.session.get(quotes_url, params=params, timeout=15)
                quote_resp.raise_for_status()
                quotes = quote_resp.json().get('quotes', {})
            except requests.exceptions.RequestException as quote_err:
                logger.warning(f"Crypto quotes fetch failed: {quote_err}")

            # Latest bars as fallback if quotes are missing
            bars = {}
            try:
                response = self.session.get(bars_url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                bars = data.get('bars', {})
            except requests.exceptions.RequestException as bar_err:
                logger.warning(f"Crypto latest bars fallback failed: {bar_err}")

            results = {}
            for symbol in symbols:
                bar = bars.get(symbol)
                daily_bar_info = daily_bars.get(symbol, {})
                current_daily = daily_bar_info.get('current')
                prev_daily = daily_bar_info.get('previous')
                quote = quotes.get(symbol)

                # Baseline: today's open from the daily bar if available, else latest bar open
                open_price = current_daily.get('o') if current_daily else None
                if open_price is None and bar:
                    open_price = bar.get('o')
                prev_close = prev_daily.get('c') if prev_daily else None
                # Fallback to current daily close if no previous day is available (e.g., weekend)
                if prev_close is None and current_daily:
                    prev_close = current_daily.get('c')
                if prev_close is None:
                    prev_close = open_price if open_price is not None else (bar.get('c') if bar else None)

                if quote:
                    bid = quote.get('bp') or 0
                    ask = quote.get('ap') or 0
                    mid = (bid + ask) / 2 if bid and ask else (ask or bid or 0)
                    quote_ts = None
                    if quote.get('t'):
                        try:
                            quote_ts = datetime.fromisoformat(quote['t'].replace('Z', '+00:00'))
                        except Exception:
                            quote_ts = None
                    last = mid
                    if quote_ts and quote_ts.date() != today and current_daily:
                        # Weekend/after-hours: prefer daily close
                        last = current_daily.get('c') or mid
                    if prev_close is None:
                        prev_close = mid
                    if open_price is None:
                        open_price = prev_close if prev_close is not None else mid
                    results[symbol] = {
                        'open': open_price if open_price is not None else mid,
                        'prev_close': prev_close,
                        'last': mid,
                        'bid': bid,
                        'ask': ask,
                        'timestamp': quote.get('t')
                    }
                elif bar:
                    # Fallback to bar close if quotes missing
                    results[symbol] = {
                        'open': open_price if open_price is not None else bar.get('o'),
                        'prev_close': prev_close,
                        'last': bar.get('c'),
                        'high': bar.get('h'),
                        'low': bar.get('l'),
                        'volume': bar.get('v'),
                        'timestamp': bar.get('t')
                    }
                elif current_daily:
                    # As a last resort, at least surface the daily open
                    results[symbol] = {
                        'open': open_price,
                        'prev_close': prev_close,
                        'last': open_price,
                        'high': current_daily.get('h'),
                        'low': current_daily.get('l'),
                        'volume': current_daily.get('v'),
                        'timestamp': current_daily.get('t')
                    }

            logger.info(f"Fetched prices for {len(results)} crypto assets")
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching crypto prices: {e}")
            return {}

    def get_prices_for_class(self, asset_class: str, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get latest prices for a list of symbols of a specific asset class.

        Args:
            asset_class: 'stocks', 'forex', or 'crypto'
            symbols: List of symbols

        Returns:
            Dict mapping symbol to price data
        """
        if not symbols:
            return {}

        # Add delay to respect rate limits
        time.sleep(config.RATE_LIMIT_DELAY)

        if asset_class == 'stocks':
            return self.get_latest_stock_prices(symbols)
        elif asset_class == 'forex':
            # Forex now sourced via Twelve Data; scheduler calls TwelveDataClient directly.
            # Keep this fallback to preserve interface if invoked elsewhere.
            try:
                from twelvedata_client import TwelveDataClient
                td_client = TwelveDataClient()
                return td_client.get_forex_quotes(symbols)
            except Exception as e:
                logger.error(f"Twelve Data forex fetch failed: {e}", exc_info=True)
                return {}
        elif asset_class == 'crypto':
            return self.get_latest_crypto_prices(symbols)
        else:
            logger.warning(f"Unknown asset class: {asset_class}")
            return {}
