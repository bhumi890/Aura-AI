"""
Shared data models used across the RAG pipeline.

Using Pydantic models (rather than loosely-typed dicts) gives us validation,
serialization, and clear contracts between pipeline stages, which matters
a lot once this module gets wired into a LangGraph Supervisor Agent.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    PDF = "pdf"
    TXT = "txt"
    MARKDOWN = "markdown"
    DOCX = "docx"


class RawDocument(BaseModel):
    """A single loaded document prior to cleaning/chunking."""

    filename: str
    source: str
    document_type: DocumentType
    text: str
    page: Optional[int] = None


class ChunkMetadata(BaseModel):
    """Metadata attached to every chunk, per project guidelines."""

    filename: str
    page: Optional[int] = None
    chunk_id: str
    source: str
    document_type: DocumentType

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class Chunk(BaseModel):
    """A single chunk of text ready for embedding."""

    content: str
    metadata: ChunkMetadata


class EmbeddedChunk(BaseModel):
    """A chunk paired with its embedding vector."""

    content: str
    metadata: ChunkMetadata
    embedding: list[float]


class RetrievedDocument(BaseModel):
    """A single retrieval result, matching the Knowledge Agent contract."""

    content: str
    metadata: dict[str, Any]
    score: float = Field(..., ge=-1.0, le=1.0)


class RetrievalResult(BaseModel):
    """The full JSON contract returned by `retrieve_knowledge`."""

    documents: list[RetrievedDocument]
