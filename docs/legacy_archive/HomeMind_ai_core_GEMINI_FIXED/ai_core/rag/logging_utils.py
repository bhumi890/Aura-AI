"""
Shared logging configuration for the RAG pipeline.

Per project guidelines, no module in this codebase uses `print()` for
diagnostic output. Everything goes through the standard `logging` module,
which is configured once here and reused everywhere via `get_logger`.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from ai_core.rag.config import settings

_CONFIGURED = False


def _configure_root_logger() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings.log_path.mkdir(parents=True, exist_ok=True)
    log_file = settings.log_path / "pipeline.log"

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler(stream=sys.stderr)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root.handlers.clear()
    root.addHandler(stream_handler)
    root.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger with consistent formatting/handlers."""
    _configure_root_logger()
    return logging.getLogger(name)
