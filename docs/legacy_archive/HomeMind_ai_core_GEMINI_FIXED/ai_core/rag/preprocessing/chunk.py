"""
Chunking module.

Splits cleaned document text into overlapping chunks using LangChain's
RecursiveCharacterTextSplitter, and stamps each chunk with full metadata.
"""

from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ai_core.rag.config import settings
from ai_core.rag.logging_utils import get_logger
from ai_core.rag.models import Chunk, RawDocument
from ai_core.rag.preprocessing.clean import clean_text
from ai_core.rag.preprocessing.metadata import build_metadata

logger = get_logger(__name__)


def _build_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )


def chunk_document(
    document: RawDocument,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Chunk]:
    """Clean and split a single RawDocument into metadata-tagged chunks."""
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    cleaned = clean_text(document.text)
    if not cleaned:
        logger.warning("Document produced no text after cleaning: %s", document.source)
        return []

    splitter = _build_splitter(chunk_size, chunk_overlap)
    raw_chunks = splitter.split_text(cleaned)

    chunks = [
        Chunk(content=raw_chunk, metadata=build_metadata(document, index, raw_chunk))
        for index, raw_chunk in enumerate(raw_chunks)
        if raw_chunk.strip()
    ]

    logger.info(
        "Chunked document %s (page=%s) into %d chunk(s)",
        document.filename,
        document.page,
        len(chunks),
    )
    return chunks


def chunk_documents(
    documents: list[RawDocument],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Chunk]:
    """Chunk a list of RawDocuments, returning a flat list of Chunk objects."""
    all_chunks: list[Chunk] = []
    for document in documents:
        all_chunks.extend(chunk_document(document, chunk_size, chunk_overlap))
    logger.info("Produced %d total chunk(s) from %d document segment(s)", len(all_chunks), len(documents))
    return all_chunks
