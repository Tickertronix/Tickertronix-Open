#!/usr/bin/env python3
"""
Raspberry Pi Hub - Headless Mode (No GUI)

Runs the API server and scheduler without the GUI interface.
Useful for:
- WSL/headless environments
- Background service operation
- Testing and development

Usage:
    python3 main_headless.py --api-key YOUR_KEY --api-secret YOUR_SECRET

    Or set credentials in database first using credentials_setup.py
"""

import sys
import logging
import signal
import argparse
import time
from pathlib import Path

import config
from db import Database
from alpaca_client import AlpacaClient
from scheduler import PriceScheduler
from api_server import run_api_server


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
    logger.info("Raspberry Pi Hub - Headless Mode")
    logger.info("=" * 70)
    logger.info(f"Database: {config.DB_PATH}")
    logger.info(f"Log file: {config.LOG_PATH}")
    logger.info(f"API endpoint: http://{config.API_HOST}:{config.API_PORT}")
    logger.info("=" * 70)

    return logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Raspberry Pi Hub - Headless Mode'
    )
    parser.add_argument(
        '--api-key',
        help='Alpaca API Key ID (or set in database)'
    )
    parser.add_argument(
        '--api-secret',
        help='Alpaca API Secret Key (or set in database)'
    )
    parser.add_argument(
        '--no-scheduler',
        action='store_true',
        help='Run API server only, without starting the scheduler'
    )
    return parser.parse_args()


# Global variables for signal handler
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

    # Parse arguments
    args = parse_args()

    # Set up logging
    logger = setup_logging()
    logger_instance = logger

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize database
        logger.info("Initializing database...")
        db = Database()

        # Get or set credentials
        if args.api_key and args.api_secret:
            logger.info("Using credentials from command line arguments")
            api_key = args.api_key
            api_secret = args.api_secret
            # Save to database for future use
            db.save_credentials(api_key, api_secret)
        else:
            logger.info("Loading credentials from database")
            api_key, api_secret = db.get_credentials()
            if not api_key or not api_secret:
                logger.error("No credentials found!")
                logger.error("Please provide credentials via:")
                logger.error("  1. Command line: --api-key KEY --api-secret SECRET")
                logger.error("  2. Or run: python3 credentials_setup.py")
                sys.exit(1)

        # Initialize Alpaca client
        logger.info("Initializing Alpaca client...")
        alpaca_client = AlpacaClient(api_key, api_secret)

        # Verify credentials
        logger.info("Verifying credentials...")
        success, message = alpaca_client.verify_credentials()
        if not success:
            logger.error(f"Credential verification failed: {message}")
            sys.exit(1)
        logger.info(f"✓ {message}")

        # Check if we have selected assets
        assets = db.get_selected_assets()
        if not assets:
            logger.warning("No assets selected for tracking!")
            logger.warning("Add assets using the GUI or database directly")
            logger.warning("API server will still start, but no prices will be fetched")

        # Initialize scheduler
        logger.info("Initializing price scheduler...")
        scheduler = PriceScheduler(db, alpaca_client)
        scheduler_instance = scheduler

        # Start local API server
        logger.info("Starting local HTTP API server...")
        api_thread = run_api_server(db, scheduler)

        # Start scheduler unless --no-scheduler flag is set
        if not args.no_scheduler:
            if assets:
                logger.info("Starting price update scheduler...")
                scheduler.start()
                logger.info(f"✓ Scheduler started - updating every {config.UPDATE_INTERVAL_MINUTES} minutes")
            else:
                logger.warning("Scheduler not started - no assets selected")
        else:
            logger.info("Scheduler disabled via --no-scheduler flag")

        # Print status
        print()
        print("=" * 70)
        print("RASPBERRY PI HUB - RUNNING")
        print("=" * 70)
        print(f"API Server: http://localhost:{config.API_PORT}")
        print(f"Selected Assets: {len(assets)}")
        print(f"Scheduler: {'Running' if scheduler.is_running else 'Stopped'}")
        print()
        print("Available endpoints:")
        print(f"  - GET http://localhost:{config.API_PORT}/health")
        print(f"  - GET http://localhost:{config.API_PORT}/prices")
        print(f"  - GET http://localhost:{config.API_PORT}/prices/stocks")
        print(f"  - GET http://localhost:{config.API_PORT}/prices/forex")
        print(f"  - GET http://localhost:{config.API_PORT}/prices/crypto")
        print(f"  - GET http://localhost:{config.API_PORT}/status")
        print()
        print("Press Ctrl+C to stop")
        print("=" * 70)
        print()

        # Keep running
        while True:
            time.sleep(1)

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
