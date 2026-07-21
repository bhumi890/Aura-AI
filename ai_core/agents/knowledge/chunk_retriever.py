"""
Agent-facing retriever wrapper.

Thin adapter between the Knowledge Agent's public interface (`knowledge.py`)
and the underlying RAG retrieval pipeline (`rag/retrieval/retriever.py`).
Kept as a separate module so the Knowledge Agent stays swappable/testable
without touching the core RAG package, and so a future Supervisor Agent can
depend on this module alone.
"""

from __future__ import annotations

from functools import lru_cache

from ai_core.rag.config import settings
from ai_core.rag.logging_utils import get_logger
from ai_core.rag.models import RetrievedDocument
from ai_core.rag.retrieval.retriever import Retriever

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_retriever() -> Retriever:
    """Lazily construct and cache a single Retriever instance (model/index load is expensive)."""
    logger.info("Initializing Retriever for Knowledge Agent")
    return Retriever()


def fetch_relevant_chunks(query: str, top_k: int | None = None) -> list[RetrievedDocument]:
    """Fetch the top_k most relevant chunks for `query` via the RAG pipeline."""
    retriever = _get_retriever()
    return retriever.retrieve(query, top_k=top_k or settings.top_k)
