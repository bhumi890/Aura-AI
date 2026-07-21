"""
Reset Database Script
Drops all tables and recreates them.

WARNING: This will delete ALL data!

Usage:
    python -m scripts.reset_database
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import create_tables, drop_tables, engine
from backend.database.models import *  # noqa: F401,F403
from backend.utils.logger import logger


async def main():
    logger.info("⚠️  Resetting database...")
    logger.info(f"   Database URL: {engine.url}")
    logger.info("")

    # Drop all tables
    logger.info("🗑️  Dropping all tables...")
    await drop_tables()
    logger.info("   ✅ All tables dropped")

    # Recreate tables
    logger.info("🔧 Recreating tables...")
    await create_tables()
    logger.info("   ✅ All tables recreated")

    logger.info("")
    logger.info("✅ Database reset complete!")


if __name__ == "__main__":
    asyncio.run(main())
