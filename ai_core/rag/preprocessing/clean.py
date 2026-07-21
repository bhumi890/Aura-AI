"""
Text cleaning utilities applied to raw document text before chunking.
"""

from __future__ import annotations

import re
import unicodedata

from ai_core.rag.logging_utils import get_logger

logger = get_logger(__name__)

_MULTI_WHITESPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(text: str) -> str:
    """
    Normalize and clean raw text extracted from a document.

    Steps:
        1. Unicode-normalize (NFKC) to collapse odd character variants.
        2. Strip control characters left over from PDF extraction.
        3. Collapse repeated horizontal whitespace.
        4. Collapse 3+ consecutive newlines down to 2 (paragraph breaks).
        5. Trim leading/trailing whitespace.
    """
    if not text:
        return ""

    normalized = unicodedata.normalize("NFKC", text)
    normalized = _CONTROL_CHARS_RE.sub("", normalized)
    normalized = _MULTI_WHITESPACE_RE.sub(" ", normalized)
    normalized = _MULTI_NEWLINE_RE.sub("\n\n", normalized)
    cleaned = normalized.strip()

    logger.debug("Cleaned text: %d chars -> %d chars", len(text), len(cleaned))
    return cleaned
