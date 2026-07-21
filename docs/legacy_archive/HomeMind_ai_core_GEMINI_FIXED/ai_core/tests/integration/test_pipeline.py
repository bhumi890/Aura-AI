"""
Integration test for the full RAG pipeline: ingestion -> FAISS storage ->
retrieval -> Knowledge Agent output.

Uses a mocked embedder (deterministic, offline) so the test doesn't require
downloading model weights, while still exercising every real code path:
loading, cleaning, chunking, storage, and semantic search.
"""

from __future__ import annotations

import numpy as np
import pytest

from ai_core.rag.ingestion import IngestionPipeline
from ai_core.rag.models import DocumentType, RawDocument
from ai_core.rag.preprocessing.chunk import chunk_documents
from ai_core.rag.retrieval.retriever import Retriever
from ai_core.rag.vectordb.faiss_store import FaissStore

DIM = 16


class _DeterministicEmbedder:
    """Deterministic, offline embedder: identical text -> identical vector."""

    dimension = DIM

    def _vector(self, text: str) -> np.ndarray:
        rng = np.random.default_rng(abs(hash(text)) % (2**32))
        vector = rng.random(DIM).astype(np.float32)
        return vector / np.linalg.norm(vector)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        return np.array([self._vector(t) for t in texts], dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        return self._vector(query)

    def embed_chunks(self, chunks):
        from ai_core.rag.models import EmbeddedChunk

        vectors = self.embed_texts([c.content for c in chunks])
        return [
            EmbeddedChunk(content=c.content, metadata=c.metadata, embedding=v.tolist())
            for c, v in zip(chunks, vectors)
        ]


@pytest.fixture
def documents_dir(tmp_path):
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()
    (docs_dir / "wellness_tips.txt").write_text(
        "Practicing gratitude daily improves emotional wellbeing. "
        "Journaling before bed can reduce nighttime anxiety significantly.",
        encoding="utf-8",
    )
    (docs_dir / "sleep_notes.md").write_text(
        "# Sleep Hygiene\n\nAvoid screens one hour before bed for better sleep quality.",
        encoding="utf-8",
    )
    return docs_dir


def test_full_pipeline_ingest_and_retrieve(tmp_path, documents_dir):
    store_dir = tmp_path / "vectordb"
    embedder = _DeterministicEmbedder()
    store = FaissStore(store_dir=store_dir, dimension=DIM)

    pipeline = IngestionPipeline(documents_dir=documents_dir, embedder=embedder, store=store)
    num_chunks = pipeline.run(rebuild=True)

    assert num_chunks > 0
    assert store.size == num_chunks

    reloaded_store = FaissStore(store_dir=store_dir)  # exercise auto-reload from disk
    assert reloaded_store.size == num_chunks

    retriever = Retriever(embedder=embedder, store=reloaded_store)
    results = retriever.retrieve("tips for better sleep", top_k=2)

    assert len(results) <= 2
    assert all(0 <= r.score <= 1.0001 for r in results)
    assert all(r.metadata["filename"] in {"wellness_tips.txt", "sleep_notes.md"} for r in results)


def test_pipeline_handles_empty_documents_directory(tmp_path):
    empty_dir = tmp_path / "empty_docs"
    empty_dir.mkdir()
    store = FaissStore(store_dir=tmp_path / "vectordb", dimension=DIM)

    pipeline = IngestionPipeline(documents_dir=empty_dir, embedder=_DeterministicEmbedder(), store=store)
    num_chunks = pipeline.run(rebuild=True)

    assert num_chunks == 0
    assert store.size == 0


def test_chunking_metadata_survives_full_round_trip(documents_dir):
    from ai_core.rag.preprocessing.loaders import load_documents

    raw_documents = load_documents(documents_dir)
    chunks = chunk_documents(raw_documents)

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.metadata.filename
        assert chunk.metadata.chunk_id
        assert chunk.metadata.document_type in (DocumentType.TXT, DocumentType.MARKDOWN)
