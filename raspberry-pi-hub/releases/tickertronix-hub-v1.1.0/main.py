#!/usr/bin/env python3
"""
Raspberry Pi Hub - Main Entry Point

A local "price hub" application for Raspberry Pi that fetches market data
from Alpaca's free-tier API and exposes it via a local HTTP API.

Usage:
    python3 main.py
"""

import sys
import logging
import signal
from pathlib import Path

import config
from db import Database
from alpaca_client import AlpacaClient
from scheduler import PriceScheduler
from api_server import run_api_server
from ui import PriceHubGUI


def setup_logging():
    """Configure application logging."""
    # Create logs directory if it doesn't exist
    Path(config.LOG_DIR).mkdir(parents=True, exist_ok=True)

    # Configure root logger
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
    logger.info("Raspberry Pi Hub - Starting Application")
    logger.info("=" * 70)
    logger.info(f"Database: {config.DB_PATH}")
    logger.info(f"Log file: {config.LOG_PATH}")
    logger.info(f"API endpoint: http://{config.API_HOST}:{config.API_PORT}")
    logger.info("=" * 70)

    return logger


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main application entry point."""
    # Set up logging
    logger = setup_logging()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize database
        logger.info("Initializing database...")
        db = Database()

        # Initialize Alpaca client
        logger.info("Initializing Alpaca client...")
        alpaca_client = AlpacaClient()

        # Check if we have stored credentials
        api_key, api_secret = db.get_credentials()
        if api_key and api_secret:
            alpaca_client.set_credentials(api_key, api_secret)
            logger.info("Loaded credentials from database")

        # Initialize scheduler
        logger.info("Initializing price scheduler...")
        scheduler = PriceScheduler(db, alpaca_client)

        # Start local API server
        logger.info("Starting local HTTP API server...")
        api_thread = run_api_server(db, scheduler)

        # Create and run GUI
        logger.info("Starting GUI...")
        gui = PriceHubGUI(db, alpaca_client, scheduler)

        # Run the GUI (this blocks until window is closed)
        gui.run()

        # Cleanup after GUI closes
        logger.info("Application shutting down...")
        scheduler.stop()
        logger.info("Scheduler stopped")

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Raspberry Pi Hub - Shutdown Complete")


if __name__ == '__main__':
    main()
