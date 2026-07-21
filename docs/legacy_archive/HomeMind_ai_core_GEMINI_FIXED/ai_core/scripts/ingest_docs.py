#!/usr/bin/env python3
"""
Ingest every document inside `rag/documents` into the FAISS vector store.

Usage:
    python scripts/ingest_docs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_core.rag.ingestion import IngestionPipeline  # noqa: E402
from ai_core.rag.logging_utils import get_logger  # noqa: E402

logger = get_logger(__name__)


def main() -> None:
    pipeline = IngestionPipeline()
    num_chunks = pipeline.run(rebuild=False)
    logger.info("ingest_docs.py finished: %d chunk(s) added/updated", num_chunks)


if __name__ == "__main__":
    main()
