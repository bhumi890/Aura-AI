"""
Ingestion pipeline orchestrator.

Wires together document loading, chunking, embedding generation, and FAISS
storage into a single reusable pipeline. Used by both `scripts/ingest_docs.py`
and `scripts/create_embeddings.py`.
"""

from __future__ import annotations

from pathlib import Path

from ai_core.rag.config import settings
from ai_core.rag.embeddings.embedder import Embedder
from ai_core.rag.logging_utils import get_logger
from ai_core.rag.preprocessing.chunk import chunk_documents
from ai_core.rag.preprocessing.loaders import load_documents
from ai_core.rag.vectordb.faiss_store import FaissStore

logger = get_logger(__name__)


class IngestionPipeline:
    """Orchestrates the full document -> chunk -> embed -> store pipeline."""

    def __init__(
        self,
        documents_dir: Path | None = None,
        embedder: Embedder | None = None,
        store: FaissStore | None = None,
    ) -> None:
        self.documents_dir = documents_dir or settings.documents_path
        self.embedder = embedder or Embedder()
        self.store = store or FaissStore(dimension=self.embedder.dimension)

    def run(self, rebuild: bool = False) -> int:
        """
        Run the full ingestion pipeline.

        Args:
            rebuild: if True, clears any existing index before ingesting
                (used by `create_embeddings.py` to rebuild from scratch).

        Returns:
            The number of chunks added to the vector store.
        """
        if rebuild:
            logger.info("Rebuild requested — clearing existing FAISS store")
            self.store.clear()

        logger.info("Starting ingestion from %s", self.documents_dir)
        raw_documents = load_documents(self.documents_dir)
        if not raw_documents:
            logger.warning("No documents found in %s — nothing to ingest", self.documents_dir)
            return 0

        chunks = chunk_documents(raw_documents)
        if not chunks:
            logger.warning("Chunking produced no chunks — nothing to embed")
            return 0

        embedded_chunks = self.embedder.embed_chunks(chunks)
        self.store.add(embedded_chunks)
        self.store.save()

        logger.info("Ingestion complete: %d chunk(s) indexed", len(embedded_chunks))
        return len(embedded_chunks)
