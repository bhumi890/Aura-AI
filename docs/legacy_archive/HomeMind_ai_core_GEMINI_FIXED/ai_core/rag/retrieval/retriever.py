"""
Retrieval pipeline.

Given a natural-language query, embeds it and performs semantic similarity
search against the persisted FAISS index, returning the top-K most similar
chunks along with their metadata and similarity scores.
"""

from __future__ import annotations

from ai_core.rag.config import settings
from ai_core.rag.embeddings.embedder import Embedder
from ai_core.rag.logging_utils import get_logger
from ai_core.rag.models import RetrievedDocument
from ai_core.rag.vectordb.faiss_store import FaissStore

logger = get_logger(__name__)


class Retriever:
    """High-level semantic retrieval interface over the FAISS vector store."""

    def __init__(self, embedder: Embedder | None = None, store: FaissStore | None = None) -> None:
        self.embedder = embedder or Embedder()
        self.store = store or FaissStore(dimension=self.embedder.dimension)

    def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievedDocument]:
        """Retrieve the top_k most semantically similar chunks for `query`."""
        top_k = top_k or settings.top_k

        if not query or not query.strip():
            logger.warning("Empty query passed to retriever")
            return []

        query_vector = self.embedder.embed_query(query)
        raw_results = self.store.search(query_vector, top_k)

        documents = [
            RetrievedDocument(content=content, metadata=metadata.as_dict(), score=score)
            for content, metadata, score in raw_results
        ]

        logger.info("Retrieved %d document(s) for query: %r", len(documents), query)
        return documents
