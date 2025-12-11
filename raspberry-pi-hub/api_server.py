"""
Local HTTP API server for exposing price data to LAN devices.
Uses Flask to provide REST endpoints for querying price information.
"""

import logging
from flask import Flask, jsonify, request
from datetime import datetime
import threading

import config
from db import Database

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global database instance (will be set when server starts)
db: Database = None
scheduler = None


def init_api(database: Database, price_scheduler):
    """
    Initialize the API with database and scheduler instances.

    Args:
        database: Database instance
        price_scheduler: PriceScheduler instance
    """
    global db, scheduler
    db = database
    scheduler = price_scheduler


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    Returns 200 if database is accessible and scheduler is initialized.
    """
    db_healthy = db.health_check() if db else False
    scheduler_running = scheduler.is_running if scheduler else False

    status = {
        'status': 'ok' if (db_healthy and scheduler_running) else 'degraded',
        'database': 'ok' if db_healthy else 'error',
        'scheduler': 'running' if scheduler_running else 'stopped',
        'timestamp': datetime.now().isoformat()
    }

    return jsonify(status), 200 if db_healthy else 503


@app.route('/prices', methods=['GET'])
def get_all_prices():
    """
    Get all tracked asset prices.

    Returns:
        JSON array of all assets with their latest prices and calculated changes.

    Example response:
    [
        {
            "symbol": "AAPL",
            "asset_class": "stocks",
            "open_price": 150.0,
            "last_price": 152.5,
            "change_amount": 2.5,
            "change_percent": 1.67,
            "last_updated": "2024-01-01T12:00:00"
        },
        ...
    ]
    """
    try:
        prices = db.get_latest_prices()
        return jsonify(prices), 200
    except Exception as e:
        logger.error(f"Error fetching all prices: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/prices/<asset_class>', methods=['GET'])
def get_prices_by_class(asset_class):
    """
    Get prices filtered by asset class.

    Args:
        asset_class: One of 'stocks', 'forex', 'crypto'

    Returns:
        JSON array of assets for the specified class
    """
    valid_classes = ['stocks', 'forex', 'crypto']
    if asset_class not in valid_classes:
        return jsonify({
            'error': f'Invalid asset class. Must be one of: {", ".join(valid_classes)}'
        }), 400

    try:
        prices = db.get_latest_prices(asset_class=asset_class)
        return jsonify(prices), 200
    except Exception as e:
        logger.error(f"Error fetching {asset_class} prices: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/prices/<asset_class>/<symbol>', methods=['GET'])
def get_price_by_symbol(asset_class, symbol):
    """
    Get price for a specific asset.

    Args:
        asset_class: One of 'stocks', 'forex', 'crypto'
        symbol: Asset symbol (e.g., 'AAPL', 'EUR/USD', 'BTCUSD')

    Returns:
        JSON object with price data for the specified asset
    """
    valid_classes = ['stocks', 'forex', 'crypto']
    if asset_class not in valid_classes:
        return jsonify({
            'error': f'Invalid asset class. Must be one of: {", ".join(valid_classes)}'
        }), 400

    try:
        # Convert symbol to uppercase for consistency
        symbol = symbol.upper()

        prices = db.get_latest_prices(asset_class=asset_class, symbol=symbol)

        if not prices:
            return jsonify({
                'error': f'No data found for {symbol} in {asset_class}'
            }), 404

        # Return the first (and should be only) result
        return jsonify(prices[0]), 200

    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/status', methods=['GET'])
def get_scheduler_status():
    """
    Get scheduler status and information.

    Returns:
        JSON object with scheduler status, last update time, next update time
    """
    try:
        if not scheduler:
            return jsonify({'error': 'Scheduler not initialized'}), 503

        status = scheduler.get_status()
        return jsonify(status), 200

    except Exception as e:
        logger.error(f"Error fetching scheduler status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/assets', methods=['GET'])
def get_selected_assets():
    """
    Get list of all selected/tracked assets.

    Query parameters:
        asset_class (optional): Filter by asset class

    Returns:
        JSON array of selected assets
    """
    try:
        asset_class = request.args.get('asset_class')
        assets = db.get_selected_assets(asset_class=asset_class)
        return jsonify(assets), 200
    except Exception as e:
        logger.error(f"Error fetching selected assets: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== Device Management Endpoints ====================

@app.route('/device/<device_id>/settings', methods=['GET'])
def get_device_settings(device_id):
    """
    Get settings for a specific device.
    If device not registered, auto-register it with defaults.

    Args:
        device_id: Device identifier (device_key from device_config.json)

    Returns:
        JSON object with device settings
    """
    try:
        # Preserve any known device metadata to avoid overwriting type/name
        existing = db.get_device_by_key(device_id)
        device_type = request.args.get('device_type') or (
            existing['device_type'] if existing and existing.get('device_type') else "matrix_portal_scroll"
        )
        device_name = request.args.get('device_name') or (
            existing['device_name'] if existing and existing.get('device_name') else f"Device {device_id[:8]}"
        )

        # Auto-register or refresh metadata/last_seen
        db.register_device(
            device_id=device_id,
            device_name=device_name,
            device_type=device_type,
            device_key=device_id
        )

        # Get settings (will return defaults if not found)
        settings = db.get_device_settings(device_id)

        return jsonify(settings), 200

    except Exception as e:
        logger.error(f"Error fetching settings for device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/device/<device_id>/settings', methods=['POST'])
def update_device_settings(device_id):
    """
    Update settings for a specific device.
    Supports partial updates - only provided fields will be changed.

    Args:
        device_id: Device identifier

    Request body: JSON with setting key-value pairs
        {
            "scroll_mode": "dual",
            "brightness": 8,
            "update_interval": 300,
            ...
        }

    Returns:
        JSON object with success status
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        settings = request.get_json()

        # Validate settings
        if 'brightness' in settings:
            if not isinstance(settings['brightness'], int) or not (1 <= settings['brightness'] <= 10):
                return jsonify({'error': 'brightness must be an integer between 1 and 10'}), 400

        if 'update_interval' in settings:
            if not isinstance(settings['update_interval'], int) or not (60 <= settings['update_interval'] <= 900):
                return jsonify({'error': 'update_interval must be an integer between 60 and 900'}), 400

        if 'scroll_mode' in settings:
            if settings['scroll_mode'] not in ['single', 'dual']:
                return jsonify({'error': 'scroll_mode must be "single" or "dual"'}), 400

        if 'scroll_speed' in settings:
            if not isinstance(settings['scroll_speed'], int) or not (10 <= settings['scroll_speed'] <= 200):
                return jsonify({'error': 'scroll_speed must be an integer between 10 and 200'}), 400

        if 'dwell_seconds' in settings:
            try:
                ds = float(settings['dwell_seconds'])
            except Exception:
                return jsonify({'error': 'dwell_seconds must be a number'}), 400
            if not (1 <= ds <= 30):
                return jsonify({'error': 'dwell_seconds must be between 1 and 30 seconds'}), 400
            settings['dwell_seconds'] = ds

        if 'asset_order' in settings:
            allowed_classes = {'stocks', 'crypto', 'forex'}
            ao = settings['asset_order']
            if isinstance(ao, str):
                ao = [x.strip() for x in ao.split(',') if x.strip()]
            if not isinstance(ao, list) or not ao:
                return jsonify({'error': 'asset_order must be a non-empty list'}), 400
            if any(a not in allowed_classes for a in ao):
                return jsonify({'error': 'asset_order entries must be stocks, crypto, or forex'}), 400
            settings['asset_order'] = ao

        # Ensure device exists (preserve known type if present)
        existing = db.get_device_by_key(device_id)
        device_type = existing['device_type'] if existing and existing.get('device_type') else "matrix_portal_scroll"
        db.register_device(
            device_id=device_id,
            device_name=f"Device {device_id[:8]}",
            device_type=device_type,
            device_key=device_id
        )

        # Update settings
        success = db.update_device_settings(device_id, settings)

        if success:
            return jsonify({'status': 'ok', 'message': 'Settings updated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update settings'}), 500

    except Exception as e:
        logger.error(f"Error updating settings for device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/device/<device_id>/heartbeat', methods=['POST'])
def device_heartbeat(device_id):
    """
    Device check-in endpoint.
    Updates last_seen timestamp for the device.

    Args:
        device_id: Device identifier

    Request body (optional):
        {
            "device_type": "matrix_portal",
            "device_name": "Living Room Display"
        }

    Returns:
        JSON object with status and settings version
    """
    try:
        # Extract optional device info from request body
        device_info = request.get_json() if request.is_json else {}
        existing = db.get_device_by_key(device_id)
        device_type = device_info.get('device_type') or (
            existing['device_type'] if existing and existing.get('device_type') else 'matrix_portal_scroll'
        )
        device_name = device_info.get('device_name') or (
            existing['device_name'] if existing and existing.get('device_name') else f"Device {device_id[:8]}"
        )

        # Register or update device info + last_seen
        db.register_device(
            device_id=device_id,
            device_name=device_name,
            device_type=device_type,
            device_key=device_id
        )

        # Get settings timestamp
        settings = db.get_device_settings(device_id)
        settings_timestamp = settings.get('updated_at') if settings else None

        return jsonify({
            'status': 'ok',
            'settings_updated_at': settings_timestamp
        }), 200

    except Exception as e:
        logger.error(f"Error processing heartbeat for device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/devices', methods=['GET'])
def list_devices():
    """
    Get all registered devices with their last seen status.

    Returns:
        JSON array of all devices
    """
    try:
        devices = db.get_all_devices()
        return jsonify(devices), 200
    except Exception as e:
        logger.error(f"Error fetching devices: {e}")
        return jsonify({'error': str(e)}), 500


# Custom error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


def run_api_server(database: Database, price_scheduler, host=config.API_HOST, port=config.API_PORT):
    """
    Start the Flask API server in a separate thread.

    Args:
        database: Database instance
        price_scheduler: PriceScheduler instance
        host: Host to bind to (default: 0.0.0.0 for LAN access)
        port: Port to listen on (default from config)
    """
    # Initialize the API with database and scheduler
    init_api(database, price_scheduler)

    # Disable Flask's default request logging (we have our own logger)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)

    logger.info(f"Starting API server on {host}:{port}")

    # Run Flask in a separate thread so it doesn't block the GUI
    server_thread = threading.Thread(
        target=lambda: app.run(host=host, port=port, debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()

    logger.info(f"API server running - accessible at http://{host}:{port}")
    logger.info("Available endpoints:")
    logger.info(f"  - GET /health")
    logger.info(f"  - GET /prices")
    logger.info(f"  - GET /prices/<asset_class>")
    logger.info(f"  - GET /prices/<asset_class>/<symbol>")
    logger.info(f"  - GET /status")
    logger.info(f"  - GET /assets")
    logger.info(f"  - GET /device/<device_id>/settings")
    logger.info(f"  - POST /device/<device_id>/settings")
    logger.info(f"  - POST /device/<device_id>/heartbeat")
    logger.info(f"  - GET /devices")

    return server_thread
