"""
Twelve Data API client (forex only).
"""

import logging
from typing import List, Dict
import requests
import time

import config

logger = logging.getLogger(__name__)


class TwelveDataClient:
    """Lightweight Twelve Data client for forex quotes."""

    def __init__(self, api_key: str = None):
        # Prefer provided key, then env/config, then DB if available
        self.api_key = api_key or config.TWELVE_DATA_API_KEY or self._load_key_from_db()
        self.base_url = config.TWELVE_DATA_BASE_URL
        self.session = requests.Session()

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def _load_key_from_db(self) -> str:
        """Try to pull key from DB config if not in env."""
        try:
            from db import Database
            db = Database(config.DB_PATH)
            return db.get_config('twelve_data_api_key')
        except Exception:
            return None

    def get_forex_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch latest forex quotes for a list of currency pairs (e.g., ['EUR/USD', 'GBP/USD']).
        Returns a dict keyed by the original symbol with open/prev_close/last/bid/ask.
        """
        if not symbols:
            return {}
        if not self.api_key:
            logger.warning("Twelve Data API key not set; skipping forex quotes")
            return {}

        # Normalize and batch
        symbols = [s.upper() for s in symbols]
        batch_size = max(1, min(config.FOREX_BATCH_SIZE, 8))
        delay_sec = max(0, config.FOREX_BATCH_DELAY_SEC)

        results: Dict[str, Dict] = {}

        for i in range(0, len(symbols), batch_size):
            chunk = symbols[i:i + batch_size]
            params = {
                'symbol': ','.join(chunk),
                'apikey': self.api_key
            }
            try:
                resp = self.session.get(
                    f"{self.base_url}/quote",
                    params=params,
                    timeout=15
                )
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.HTTPError as e:
                status = getattr(resp, "status_code", None)
                logger.error(f"Twelve Data quotes failed ({status}): {e}")
                continue
            except requests.exceptions.RequestException as e:
                logger.error(f"Twelve Data quotes request error: {e}")
                continue

            # The response may be a dict keyed by symbol or a single dict; handle both
            parsed = {}
            if isinstance(data, dict) and all(k in data for k in ['symbol', 'price']):
                parsed[data['symbol'].upper()] = data
            elif isinstance(data, dict):
                # assume multi-symbol: { "EUR/USD": {...}, "GBP/USD": {...} }
                parsed = {k.upper(): v for k, v in data.items() if isinstance(v, dict)}

            for sym, quote in parsed.items():
                last = float(quote.get('price') or quote.get('close') or 0)
                prev_close = float(quote.get('previous_close') or last)
                bid = float(quote.get('bid') or 0)
                ask = float(quote.get('ask') or 0)
                open_price = prev_close

                if last:
                    results[sym] = {
                        'open': open_price,
                        'prev_close': prev_close,
                        'last': last,
                        'bid': bid,
                        'ask': ask,
                        'timestamp': quote.get('datetime') or quote.get('timestamp')
                    }

            if delay_sec and i + batch_size < len(symbols):
                time.sleep(delay_sec)

        return results
