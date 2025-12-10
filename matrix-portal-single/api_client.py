"""
Local Hub API client for Matrix Portal (single-panel build).
Fetches prices and per-device settings from the local Raspberry Pi hub.
"""

import json
import os

try:
    import adafruit_requests
except Exception:
    adafruit_requests = None


class LocalHubAPI:
    """Lightweight client for the local hub (no auth)."""

    def __init__(self, requests_session, base_url=None):
        self.session = requests_session
        default_base = "http://tickertronixhub.local:5001"
        self.base_url = (base_url or self._load_base_url() or default_base).rstrip('/')
        self.settings_version = None
        self.should_refresh_settings = False
        try:
            print("[HUB] Using base URL:", self.base_url)
        except Exception:
            pass

    def _load_base_url(self):
        try:
            with open('device_config.json', 'r') as f:
                cfg = json.loads(f.read())
                hub = cfg.get('hub_base_url')
                if hub:
                    return hub
        except Exception:
            pass
        try:
            hub_env = os.getenv("HUB_BASE_URL")
            if hub_env:
                return hub_env
        except Exception:
            pass
        try:
            with open('hub_url.txt', 'r') as f:
                url = f.read().strip()
                if url:
                    return url
        except Exception:
            pass
        try:
            import wifi
            gw = getattr(wifi.radio, "ipv4_gateway", None)
            if gw:
                return f"http://{gw}:5001"
        except Exception:
            pass
        return None

    def send_heartbeat(self):
        """Send periodic heartbeat to hub with device identification."""
        if not self.session:
            return False

        device_id = None
        device_type = "matrix_portal_single"
        device_name = None
        try:
            with open('device_config.json', 'r') as f:
                cfg = json.loads(f.read()) or {}
                device_id = cfg.get('device_key') or cfg.get('device_id')
                device_type = cfg.get('device_type', device_type)
                device_name = cfg.get('device_name')
        except Exception:
            pass

        if not device_id:
            return False

        try:
            resp = self.session.post(
                f"{self.base_url}/device/{device_id}/heartbeat",
                json={"device_type": device_type, "device_name": device_name},
                timeout=5
            )
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    hub_ts = data.get('settings_updated_at')
                    if hub_ts and hub_ts != self.settings_version:
                        self.should_refresh_settings = True
                except Exception:
                    pass
                return True
            try:
                print(f"[HUB] Heartbeat failed: HTTP {resp.status_code}")
            except Exception:
                pass
            return False
        except Exception as e:
            try:
                print(f"[HUB] Heartbeat error: {e}")
            except Exception:
                pass
            return False

    def get_display_settings(self):
        """
        Fetch display settings from hub, falling back to local config.
        Priority: Hub settings > device_config.json > hardcoded defaults
        """
        defaults = {
            'brightness': 10,
            'update_interval': 300,
            'dwell_seconds': 3,
            'asset_order': ['stocks', 'crypto', 'forex'],
            'font': 'default'
        }

        device_id = None
        try:
            with open('device_config.json', 'r') as f:
                cfg = json.loads(f.read()) or {}
                device_id = cfg.get('device_key') or cfg.get('device_id')
                for k in defaults.keys():
                    if k in cfg:
                        defaults[k] = cfg[k]
        except Exception:
            pass

        if device_id and self.session:
            try:
                resp = self.session.get(f"{self.base_url}/device/{device_id}/settings", timeout=5)
                if resp.status_code == 200:
                    hub_settings = resp.json()
                    defaults.update(hub_settings)
                    self.settings_version = hub_settings.get('updated_at') or self.settings_version
                    self.should_refresh_settings = False
                    try:
                        print(f"[HUB] Fetched settings from hub for device {device_id}")
                    except Exception:
                        pass
                else:
                    try:
                        print(f"[HUB] Settings fetch failed: HTTP {resp.status_code}")
                    except Exception:
                        pass
            except Exception as e:
                try:
                    print(f"[HUB] Error fetching settings: {e}")
                except Exception:
                    pass

        return defaults

    def get_ticker_data(self):
        """Fetch prices from local hub and map to ticker format."""
        if not self.session:
            return {}
        try:
            resp = self.session.get(f"{self.base_url}/prices", timeout=10)
            if resp.status_code != 200:
                print(f"[HUB] HTTP error {resp.status_code}")
                return {}
            data = resp.json()
            if isinstance(data, list):
                return {'tickers': data}
            return {}
        except Exception as e:
            try:
                print("[HUB] Error fetching prices:", e)
            except Exception:
                pass
            return {}

    def get_device_config(self):
        try:
            with open('device_config.json', 'r') as f:
                return json.loads(f.read())
        except Exception:
            return {}

    def parse_ticker_data(self, ticker_data):
        stocks = []
        crypto = []
        forex = []
        if not ticker_data:
            return stocks, crypto, forex
        try:
            for item in ticker_data.get('tickers', []):
                cls = (item.get('asset_class') or '').lower()
                symbol = item.get('symbol') or item.get('ticker') or ''
                price = float(item.get('last_price') or item.get('last') or item.get('lastPrice') or 0)
                change_amt = float(item.get('change_amount') or item.get('change') or 0)
                change_pct = float(item.get('change_percent') or 0)
                if cls.startswith('stock'):
                    stocks.append({'ticker': symbol, 'tngoLast': price, 'prcChange': change_amt})
                elif cls == 'crypto':
                    crypto.append({'ticker': symbol.upper(), 'lastPrice': price, 'prcChangePct': change_pct})
                elif cls == 'forex':
                    forex.append({'ticker': symbol.upper(), 'mid_price': "{:.4f}".format(price if price else 0)})
        except Exception as e:
            try:
                print("[HUB] Parse error:", e)
            except Exception:
                pass
        return stocks, crypto, forex

    # Compatibility no-ops
    def get_last_claim_code(self):
        return None

    def recover_device(self):
        return False

    def request_claim_token(self):
        return None
