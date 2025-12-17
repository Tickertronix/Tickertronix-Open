#!/usr/bin/env python3
"""
Web-based UI for Raspberry Pi Hub.
Access via browser - works on Windows, WSL, and Raspberry Pi.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import logging
import os
import socket
from datetime import datetime
import config
from db import Database
from alpaca_client import AlpacaClient
from scheduler import PriceScheduler
from twelvedata_client import TwelveDataClient

logger = logging.getLogger(__name__)

# Create Flask app with static folder
web_app = Flask(__name__, static_folder='static', static_url_path='/static')
web_app.secret_key = 'raspberry-pi-hub-secret-key-change-in-production'

# Global instances (set by init_web_ui)
db = None
alpaca_client = None
scheduler = None


def _guess_hub_url():
    """Best-effort guess of the hub base URL for LAN devices."""
    def _private_ip_candidates():
        addrs = set()
        try:
            for info in socket.getaddrinfo(None, 0, socket.AF_INET, socket.SOCK_DGRAM):
                addrs.add(info[4][0])
        except Exception:
            pass
        try:
            addrs.add(socket.gethostbyname(socket.gethostname()))
        except Exception:
            pass
        # Filter private ranges
        priv = []
        for ip in addrs:
            if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("172."):
                priv.append(ip)
        return priv

    host_ip = request.host.split(":")[0] if request else None
    env_ip = os.environ.get("HUB_LAN_IP")
    priv_ips = _private_ip_candidates()
    lan_ip = env_ip or (priv_ips[0] if priv_ips else None)

    base_ip = lan_ip or (host_ip if host_ip not in (None, "127.0.0.1", "localhost") else config.HUB_BASE_HOST)
    host_base = f"http://{host_ip}:{config.API_PORT}" if host_ip else f"http://localhost:{config.API_PORT}"
    lan_base = f"http://{lan_ip}:{config.API_PORT}" if lan_ip else None
    priv_bases = [f"http://{ip}:{config.API_PORT}" for ip in priv_ips]
    chosen = f"http://{base_ip}:{config.API_PORT}"

    return {
        'chosen': chosen,
        'lan_base': lan_base,
        'host_base': host_base,
        'priv_bases': priv_bases
    }


def init_web_ui(database, client, price_scheduler):
    """Initialize web UI with database and scheduler."""
    global db, alpaca_client, scheduler
    db = database
    alpaca_client = client
    scheduler = price_scheduler


@web_app.route('/')
def index():
    """Main dashboard."""
    # Check if credentials exist
    api_key, api_secret = db.get_credentials()
    has_credentials = bool(api_key and api_secret)

    # Get selected assets
    assets = db.get_selected_assets()
    assets_by_class = {
        'stocks': [a for a in assets if a['asset_class'] == 'stocks'],
        'forex': [a for a in assets if a['asset_class'] == 'forex'],
        'crypto': [a for a in assets if a['asset_class'] == 'crypto']
    }

    # Get scheduler status
    scheduler_status = scheduler.get_status() if scheduler else None

    # Get latest prices
    prices = db.get_latest_prices()
    hub_guess = _guess_hub_url()
    hub_base_url = hub_guess['chosen']
    hub_prices_url = f"{hub_base_url}/prices"

    return render_template('dashboard.html',
                         has_credentials=has_credentials,
                         assets_by_class=assets_by_class,
                         scheduler_status=scheduler_status,
                         prices=prices,
                         config=config,
                         hub_base_url=hub_base_url,
                         hub_prices_url=hub_prices_url,
                         hub_guess=hub_guess)


@web_app.route('/credentials', methods=['GET', 'POST'])
def credentials():
    """Credentials setup page."""
    if request.method == 'POST':
        action = request.form.get('action') or 'alpaca'

        if action == 'save_twelve_key':
            twelve_key = request.form.get('twelve_api_key', '').strip()
            if not twelve_key:
                return jsonify({'success': False, 'message': 'Twelve Data key is required'})
            db.save_config('twelve_data_api_key', twelve_key)
            return jsonify({'success': True, 'message': 'Twelve Data key saved'})

        api_key = request.form.get('api_key', '').strip()
        api_secret = request.form.get('api_secret', '').strip()
        twelve_key = request.form.get('twelve_api_key', '').strip()

        if not api_key or not api_secret:
            return jsonify({'success': False, 'message': 'Both fields are required'})

        # Verify Alpaca credentials
        alpaca_client.set_credentials(api_key, api_secret)
        success, message = alpaca_client.verify_credentials()

        if success:
            db.save_credentials(api_key, api_secret)
            if twelve_key:
                db.save_config('twelve_data_api_key', twelve_key)
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message})

    # GET request
    api_key, api_secret = db.get_credentials()
    twelve_key = db.get_config('twelve_data_api_key')
    return render_template('credentials.html',
                         api_key=api_key[:10] + '...' if api_key else None,
                         twelve_key=twelve_key[:6] + '...' if twelve_key else None)


@web_app.route('/assets', methods=['GET', 'POST'])
def assets():
    """Asset selection page."""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'fetch_assets':
            asset_class = request.form.get('asset_class')

            if asset_class == 'stocks':
                available = alpaca_client.get_stock_assets()
            elif asset_class == 'forex':
                available = alpaca_client.get_forex_assets()
            elif asset_class == 'crypto':
                available = alpaca_client.get_crypto_assets()
            else:
                return jsonify({'success': False, 'message': 'Invalid asset class'})

            return jsonify({'success': True, 'assets': available})

        elif action == 'add_asset':
            symbol = request.form.get('symbol')
            asset_class = request.form.get('asset_class')

            # Check limit
            count = db.count_selected_assets(asset_class)
            if count >= config.MAX_ASSETS_PER_CLASS:
                return jsonify({
                    'success': False,
                    'message': f'Maximum {config.MAX_ASSETS_PER_CLASS} assets per class'
                })

            # Add asset to database
            db.add_selected_asset(symbol, asset_class)

            # Immediately fetch price data for the newly added asset
            price_fetched = False
            try:
                price_data = alpaca_client.get_prices_for_class(asset_class, [symbol])
                if price_data and symbol in price_data:
                    data = price_data[symbol]
                    open_price = data.get('open', 0)
                    last_price = data.get('last', 0)

                    if open_price and last_price:
                        db.update_price(symbol, asset_class, open_price, last_price)
                        logger.info(f'Fetched initial price for {symbol}: ${last_price}')
                        price_fetched = True
            except Exception as e:
                logger.warning(f'Could not fetch initial price for {symbol}: {e}')

            message = f'Added {symbol}'
            if price_fetched:
                message += ' with current price data'

            return jsonify({'success': True, 'message': message})

        elif action == 'remove_asset':
            symbol = request.form.get('symbol')
            asset_class = request.form.get('asset_class')
            db.remove_selected_asset(symbol, asset_class)
            return jsonify({'success': True, 'message': f'Removed {symbol}'})

        elif action == 'set_asset_status':
            symbol = request.form.get('symbol')
            asset_class = request.form.get('asset_class')
            enabled = request.form.get('enabled') == 'true'
            db.set_asset_enabled(symbol, asset_class, enabled)
            return jsonify({'success': True, 'message': f"{symbol} {'activated' if enabled else 'deactivated'}"})

        elif action == 'start_scheduler':
            if not scheduler.is_running:
                assets = db.get_selected_assets()
                if assets:
                    scheduler.start()
                    return jsonify({'success': True, 'message': 'Scheduler started'})
                else:
                    return jsonify({'success': False, 'message': 'No assets selected'})
            return jsonify({'success': False, 'message': 'Already running'})

    # GET request
    assets = db.get_selected_assets(include_disabled=True)
    assets_by_class = {
        'stocks': [a for a in assets if a['asset_class'] == 'stocks'],
        'forex': [a for a in assets if a['asset_class'] == 'forex'],
        'crypto': [a for a in assets if a['asset_class'] == 'crypto']
    }

    return render_template('assets.html',
                         assets_by_class=assets_by_class,
                         config=config)


@web_app.route('/prices')
def prices_view():
    """Prices display page."""
    prices = db.get_latest_prices()
    scheduler_status = scheduler.get_status() if scheduler else None

    return render_template('prices.html',
                         prices=prices,
                         scheduler_status=scheduler_status)


@web_app.route('/devices', methods=['GET', 'POST'])
def devices():
    """Device management page."""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'list_devices':
            devices = db.get_all_devices()
            return jsonify({'success': True, 'devices': devices})

        elif action == 'get_settings':
            device_id = request.form.get('device_id')
            settings = db.get_device_settings(device_id)
            return jsonify({'success': True, 'settings': settings})

        elif action == 'update_settings':
            device_id = request.form.get('device_id')

            # Collect settings from form
            settings = {}
            if 'scroll_mode' in request.form:
                settings['scroll_mode'] = request.form.get('scroll_mode')
            if 'scroll_speed' in request.form:
                settings['scroll_speed'] = int(request.form.get('scroll_speed'))
            if 'brightness' in request.form:
                settings['brightness'] = int(request.form.get('brightness'))
            if 'update_interval' in request.form:
                settings['update_interval'] = int(request.form.get('update_interval'))
            if 'dwell_seconds' in request.form:
                try:
                    settings['dwell_seconds'] = float(request.form.get('dwell_seconds'))
                except Exception:
                    settings['dwell_seconds'] = None
            if 'top_sources' in request.form:
                # Checkboxes send multiple values
                settings['top_sources'] = request.form.getlist('top_sources')
            if 'bottom_sources' in request.form:
                settings['bottom_sources'] = request.form.getlist('bottom_sources')
            if 'font' in request.form:
                settings['font'] = request.form.get('font')
            if 'asset_order' in request.form:
                raw_order = request.form.get('asset_order', '')
                settings['asset_order'] = [s.strip() for s in raw_order.split(',') if s.strip()]

            success = db.update_device_settings(device_id, settings)
            if success:
                return jsonify({'success': True, 'message': 'Settings updated successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to update settings'})

        elif action == 'enable_device':
            device_id = request.form.get('device_id')
            enabled = request.form.get('enabled') == 'true'
            db.enable_device(device_id, enabled)
            return jsonify({'success': True, 'message': f"Device {'enabled' if enabled else 'disabled'}"})

        elif action == 'touch_settings':
            device_id = request.form.get('device_id')
            db.touch_device_settings(device_id)
            return jsonify({'success': True, 'message': 'Settings timestamp updated. Device will refresh on next heartbeat.'})

    # GET request
    devices = db.get_all_devices()
    return render_template('devices.html', devices=devices)


@web_app.route('/api/prices')
def api_prices():
    """API endpoint for prices (for AJAX updates)."""
    asset_class = request.args.get('asset_class')
    prices = db.get_latest_prices(asset_class=asset_class)
    return jsonify(prices)


@web_app.route('/api/status')
def api_status():
    """API endpoint for scheduler status."""
    status = scheduler.get_status() if scheduler else {'is_running': False}
    return jsonify(status)


@web_app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """Trigger an immediate price refresh."""
    if not scheduler:
        return jsonify({'success': False, 'message': 'Scheduler not initialized'}), 500

    try:
        scheduler.update_all_prices()
        # Also refresh forex (Twelve Data) immediately
        scheduler.update_forex_prices()
        return jsonify({'success': True, 'message': 'Prices refreshed'})
    except Exception as e:
        logger.error(f"Manual refresh failed: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    # This is for standalone testing
    logging.basicConfig(level=logging.INFO)
    db = Database()
    alpaca_client = AlpacaClient()
    scheduler = PriceScheduler(db, alpaca_client)
    init_web_ui(db, alpaca_client, scheduler)
    web_app.run(host='0.0.0.0', port=8080, debug=True)
