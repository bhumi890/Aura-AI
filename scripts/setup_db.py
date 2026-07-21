"""
Setup Database Script
Creates all database tables.

Usage:
    python -m scripts.setup_db
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import create_tables, engine
from backend.database.models import *  # noqa: F401,F403 — Import all models so they register with Base
from backend.utils.logger import logger


async def main():
    logger.info("🔧 Setting up database...")
    logger.info(f"   Database URL: {engine.url}")

    await create_tables()

    logger.info("✅ All tables created successfully!")
    logger.info("")
    logger.info("   Tables created:")
    logger.info("   • users")
    logger.info("   • conversations")
    logger.info("   • messages")
    logger.info("   • journal_entries")
    logger.info("   • mood_logs")
    logger.info("   • wellness_plans")


if __name__ == "__main__":
    asyncio.run(main())
