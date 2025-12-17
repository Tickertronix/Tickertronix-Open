#!/usr/bin/env python3
"""
Raspberry Pi Hub - Web UI Mode

Runs both the Web UI (port 8080) and REST API (port 5001).
Access via browser - works on Windows, WSL, and Raspberry Pi.

Usage:
    python3 main_web.py

Then open: http://localhost:8080
"""

import sys
import logging
import signal
from pathlib import Path
from threading import Thread

import config
from db import Database
from alpaca_client import AlpacaClient
from scheduler import PriceScheduler
from api_server import run_api_server
from web_ui import web_app, init_web_ui


def setup_logging():
    """Configure application logging."""
    Path(config.LOG_DIR).mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(config.LOG_PATH),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 70)
    logger.info("Raspberry Pi Hub - Web UI Mode")
    logger.info("=" * 70)
    logger.info(f"Database: {config.DB_PATH}")
    logger.info(f"Log file: {config.LOG_PATH}")
    logger.info(f"Web UI: http://localhost:8080")
    logger.info(f"REST API: http://localhost:{config.API_PORT}")
    logger.info("=" * 70)

    return logger


# Global instances for signal handler
scheduler_instance = None
logger_instance = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    if logger_instance:
        logger_instance.info(f"Received signal {signum}, shutting down...")
    if scheduler_instance:
        scheduler_instance.stop()
    sys.exit(0)


def main():
    """Main application entry point."""
    global scheduler_instance, logger_instance

    # Set up logging
    logger = setup_logging()
    logger_instance = logger

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize database
        logger.info("Initializing database...")
        db = Database()

        # Initialize Alpaca client
        logger.info("Initializing Alpaca client...")
        alpaca_client = AlpacaClient()

        # Load credentials if they exist
        api_key, api_secret = db.get_credentials()
        if api_key and api_secret:
            alpaca_client.set_credentials(api_key, api_secret)
            logger.info("Loaded credentials from database")

        # Initialize scheduler
        logger.info("Initializing price scheduler...")
        scheduler = PriceScheduler(db, alpaca_client)
        scheduler_instance = scheduler

        # Auto-start scheduler on boot when credentials exist
        assets = db.get_selected_assets()
        if api_key and api_secret:
            try:
                if assets:
                    logger.info(f"Auto-starting scheduler for {len(assets)} assets...")
                else:
                    logger.info("Auto-starting scheduler (no assets selected yet; will idle until assets are added)...")
                scheduler.start()
                logger.info(f"Scheduler running - interval {config.UPDATE_INTERVAL_MINUTES} minutes")
            except Exception as e:
                logger.error(f"Failed to auto-start scheduler: {e}", exc_info=True)
        else:
            logger.warning("Scheduler not started automatically: missing Alpaca credentials")

        # Start REST API server (background thread)
        logger.info("Starting REST API server...")
        api_thread = run_api_server(db, scheduler)

        # Initialize Web UI
        logger.info("Initializing Web UI...")
        init_web_ui(db, alpaca_client, scheduler)

        # Disable Flask request logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)

        # Print startup info
        print()
        print("=" * 70)
        print("🚀 RASPBERRY PI HUB - WEB UI")
        print("=" * 70)
        print()
        print("✅ Application is running!")
        print()
        print("Access the Web UI:")
        print("  🌐 http://localhost:8080")
        print()
        print("REST API endpoint:")
        print(f"  🔌 http://localhost:{config.API_PORT}")
        print()
        print("From other devices on your network, use your PC's IP:")
        print("  💻 http://YOUR_PC_IP:8080")
        print(f"  🔌 http://YOUR_PC_IP:{config.API_PORT}")
        print()
        print("Press Ctrl+C to stop")
        print("=" * 70)
        print()

        # Start Web UI (blocking)
        web_app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if scheduler_instance:
            scheduler_instance.stop()
        logger.info("Raspberry Pi Hub - Shutdown Complete")


if __name__ == '__main__':
    main()
