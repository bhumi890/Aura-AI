"""
Knowledge Retrieval Agent (Agent 3).

This module exposes exactly one public function, `retrieve_knowledge`,
which is the sole integration point for other agents (e.g. a LangGraph
Supervisor Agent). It returns pure JSON-serializable data — no
explanations, no markdown, no print statements — so it can be called
directly from an agent graph node or an API route.

Contract
--------
    retrieve_knowledge(query: str) -> dict

    {
        "documents": [
            {
                "content": "...",
                "metadata": {...},
                "score": 0.87
            }
        ]
    }

On any internal failure, an empty `{"documents": []}` payload is returned
rather than raising, so a single bad query cannot crash a calling agent
graph. All diagnostic information goes to the logger, never to stdout.
"""

from __future__ import annotations

from typing import Any

from ai_core.agents.knowledge.formatter import empty_response, format_response
from ai_core.agents.knowledge.chunk_retriever import fetch_relevant_chunks
from ai_core.rag.logging_utils import get_logger

logger = get_logger(__name__)

__all__ = ["retrieve_knowledge"]


def retrieve_knowledge(query: str) -> dict[str, Any]:
    """
    Retrieve the most relevant knowledge chunks for `query`.

    Args:
        query: A natural-language query string.

    Returns:
        A JSON-serializable dict matching the Knowledge Agent contract:
        {"documents": [{"content": str, "metadata": dict, "score": float}, ...]}
    """
    if not isinstance(query, str) or not query.strip():
        logger.warning("retrieve_knowledge called with an empty or invalid query")
        return empty_response()

    try:
        documents = fetch_relevant_chunks(query)
        return format_response(documents)
    except Exception:
        logger.exception("retrieve_knowledge failed for query: %r", query)
        return empty_response()
