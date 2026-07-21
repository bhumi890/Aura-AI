"""
Logger Utility
Structured logging for the backend application.
"""

import logging
import sys
from datetime import datetime


def setup_logger(name: str = "wellness_companion", level: int = logging.INFO) -> logging.Logger:
    """
    Creates a structured logger with console output.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# ── Pre-configured loggers ────────────────────────────────────
logger = setup_logger("wellness_companion")
api_logger = setup_logger("wellness_companion.api")
db_logger = setup_logger("wellness_companion.db")
voice_logger = setup_logger("wellness_companion.voice")
