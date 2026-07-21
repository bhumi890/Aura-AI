"""Unit tests for rag.vectordb.faiss_store and rag.retrieval.retriever"""

from __future__ import annotations

import numpy as np
import pytest

from ai_core.rag.models import ChunkMetadata, DocumentType, EmbeddedChunk
from ai_core.rag.retrieval.retriever import Retriever
from ai_core.rag.vectordb.faiss_store import FaissStore

DIM = 4


def _make_embedded_chunk(content: str, vector: list[float], chunk_id: str) -> EmbeddedChunk:
    metadata = ChunkMetadata(
        filename="doc.txt",
        page=None,
        chunk_id=chunk_id,
        source="/tmp/doc.txt",
        document_type=DocumentType.TXT,
    )
    return EmbeddedChunk(content=content, metadata=metadata, embedding=vector)


@pytest.fixture
def store(tmp_path):
    return FaissStore(store_dir=tmp_path / "vectordb", dimension=DIM)


def test_faiss_store_add_and_search(store):
    chunks = [
        _make_embedded_chunk("anxiety coping strategies", [1.0, 0.0, 0.0, 0.0], "c1"),
        _make_embedded_chunk("sleep hygiene tips", [0.0, 1.0, 0.0, 0.0], "c2"),
    ]
    store.add(chunks)

    results = store.search(np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32), top_k=2)

    assert len(results) == 2
    top_content, top_metadata, top_score = results[0]
    assert top_content == "anxiety coping strategies"
    assert top_metadata.chunk_id == "c1"
    assert top_score == pytest.approx(1.0, abs=1e-4)


def test_faiss_store_persists_and_reloads(tmp_path):
    store_dir = tmp_path / "vectordb"
    store_a = FaissStore(store_dir=store_dir, dimension=DIM)
    store_a.add([_make_embedded_chunk("persisted content", [0.0, 0.0, 1.0, 0.0], "c1")])
    store_a.save()

    store_b = FaissStore(store_dir=store_dir)  # no dimension passed -> must reload from disk
    assert store_b.size == 1

    results = store_b.search(np.array([0.0, 0.0, 1.0, 0.0], dtype=np.float32), top_k=1)
    assert results[0][0] == "persisted content"


def test_faiss_store_search_on_empty_index_returns_empty_list(store):
    results = store.search(np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32), top_k=5)
    assert results == []


def test_faiss_store_clear_removes_persisted_files(tmp_path):
    store_dir = tmp_path / "vectordb"
    store = FaissStore(store_dir=store_dir, dimension=DIM)
    store.add([_make_embedded_chunk("temp content", [1.0, 1.0, 0.0, 0.0], "c1")])
    store.save()

    store.clear()

    assert store.size == 0
    assert not (store_dir / "index.faiss").exists()


class _FakeEmbedder:
    """Fake embedder returning fixed vectors keyed by exact query text."""

    dimension = DIM

    def embed_query(self, query: str) -> np.ndarray:
        if "anxiety" in query:
            return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        return np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)


def test_retriever_returns_retrieved_documents(store):
    store.add(
        [
            _make_embedded_chunk("how to manage anxiety", [1.0, 0.0, 0.0, 0.0], "c1"),
            _make_embedded_chunk("improving sleep quality", [0.0, 1.0, 0.0, 0.0], "c2"),
        ]
    )
    retriever = Retriever(embedder=_FakeEmbedder(), store=store)

    results = retriever.retrieve("tips for anxiety relief", top_k=1)

    assert len(results) == 1
    assert results[0].content == "how to manage anxiety"
    assert results[0].metadata["chunk_id"] == "c1"
    assert -1.0 <= results[0].score <= 1.0


def test_retriever_empty_query_returns_no_documents(store):
    retriever = Retriever(embedder=_FakeEmbedder(), store=store)
    assert retriever.retrieve("   ") == []
