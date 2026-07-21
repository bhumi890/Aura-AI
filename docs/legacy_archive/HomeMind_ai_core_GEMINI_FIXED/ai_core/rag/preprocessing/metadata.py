"""
Metadata extraction helpers.

Every chunk produced by this pipeline is stamped with: filename, page,
chunk_id, source, and document_type, as required by the project
specification.
"""

from __future__ import annotations

import hashlib

from ai_core.rag.models import ChunkMetadata, DocumentType, RawDocument


def build_chunk_id(filename: str, page: int | None, chunk_index: int, content: str) -> str:
    """
    Build a deterministic, collision-resistant chunk id.

    Deterministic ids (rather than random UUIDs) mean re-ingesting the same
    document produces the same chunk ids, which makes deduplication and
    incremental re-indexing straightforward.
    """
    digest_source = f"{filename}:{page}:{chunk_index}:{content[:64]}"
    digest = hashlib.sha1(digest_source.encode("utf-8")).hexdigest()[:12]
    return f"{filename}-{page if page is not None else 0}-{chunk_index}-{digest}"


def build_metadata(
    document: RawDocument,
    chunk_index: int,
    content: str,
) -> ChunkMetadata:
    """Construct a ChunkMetadata object for a chunk derived from `document`."""
    return ChunkMetadata(
        filename=document.filename,
        page=document.page,
        chunk_id=build_chunk_id(document.filename, document.page, chunk_index, content),
        source=document.source,
        document_type=DocumentType(document.document_type),
    )
