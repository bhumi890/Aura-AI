"""Unit tests for rag.preprocessing.chunk"""

from __future__ import annotations

from ai_core.rag.models import DocumentType, RawDocument
from ai_core.rag.preprocessing.chunk import chunk_document, chunk_documents


def _make_document(text: str, filename: str = "sample.txt") -> RawDocument:
    return RawDocument(
        filename=filename,
        source=f"/tmp/{filename}",
        document_type=DocumentType.TXT,
        text=text,
        page=None,
    )


def test_chunk_document_returns_chunks_for_long_text():
    long_text = "This is a sentence about wellness and mindfulness. " * 100
    document = _make_document(long_text)

    chunks = chunk_document(document, chunk_size=200, chunk_overlap=50)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.content.strip() != ""
        assert len(chunk.content) <= 200 + 50  # allow splitter overshoot tolerance


def test_chunk_document_preserves_metadata_fields():
    document = _make_document("Short piece of wellness content.", filename="notes.md")
    chunks = chunk_document(document, chunk_size=500, chunk_overlap=100)

    assert len(chunks) == 1
    metadata = chunks[0].metadata
    assert metadata.filename == "notes.md"
    assert metadata.source == "/tmp/notes.md"
    assert metadata.document_type == DocumentType.TXT
    assert metadata.chunk_id  # non-empty


def test_chunk_document_empty_text_returns_no_chunks():
    document = _make_document("   \n\n   ")
    chunks = chunk_document(document)
    assert chunks == []


def test_chunk_documents_aggregates_across_multiple_documents():
    docs = [
        _make_document("Content about anxiety and coping strategies. " * 20, filename="a.txt"),
        _make_document("Content about sleep hygiene and relaxation. " * 20, filename="b.txt"),
    ]
    chunks = chunk_documents(docs, chunk_size=200, chunk_overlap=50)

    filenames = {chunk.metadata.filename for chunk in chunks}
    assert filenames == {"a.txt", "b.txt"}
    assert len(chunks) > 2


def test_chunk_ids_are_unique_within_a_document():
    long_text = "Unique sentence marker number {} for testing purposes. ".format
    text = " ".join(long_text(i) for i in range(50))
    document = _make_document(text)

    chunks = chunk_document(document, chunk_size=150, chunk_overlap=20)
    chunk_ids = [c.metadata.chunk_id for c in chunks]

    assert len(chunk_ids) == len(set(chunk_ids))
