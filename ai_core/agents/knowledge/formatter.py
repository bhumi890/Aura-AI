"""
Response formatter for the Knowledge Agent.

Validates and shapes retrieval results into the exact JSON contract
expected by downstream agents (e.g. a future Supervisor Agent):

{
    "documents": [
        {"content": "...", "metadata": {...}, "score": 0.87}
    ]
}
"""

from __future__ import annotations

from typing import Any

from ai_core.rag.logging_utils import get_logger
from ai_core.rag.models import RetrievalResult, RetrievedDocument

logger = get_logger(__name__)


def format_response(documents: list[RetrievedDocument]) -> dict[str, Any]:
    """
    Build the final JSON-serializable response dict.

    Runs the result set through the `RetrievalResult` Pydantic model so any
    malformed data is caught here rather than leaking to the caller.
    """
    result = RetrievalResult(documents=documents)
    payload = result.model_dump(mode="json")
    logger.debug("Formatted knowledge agent response with %d document(s)", len(documents))
    return payload


def empty_response() -> dict[str, Any]:
    """Return a well-formed empty response (used for empty/invalid queries or errors)."""
    return format_response([])
