#!/usr/bin/env python3
"""Utility script to prune old price history from the local database."""

import logging
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config
from db import Database


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info(
        "Starting price history cleanup (retaining last %s days)...",
        config.PRICE_RETENTION_DAYS,
    )

    db = Database()
    removed = db.cleanup_price_history()
    logger.info("Cleanup complete. Removed %s old rows.", removed)


if __name__ == "__main__":
    main()
