"""
Unit tests for rag.embeddings.embedder

The real sentence-transformers model is mocked out so these tests run fast
and do not require downloading model weights or network access.
"""

from __future__ import annotations

import numpy as np
import pytest

from ai_core.rag.embeddings import embedder as embedder_module
from ai_core.rag.models import Chunk, ChunkMetadata, DocumentType


class _FakeSentenceTransformer:
    """A drop-in fake for SentenceTransformer that returns deterministic vectors."""

    def __init__(self, *_args, **_kwargs):
        self._dim = 8

    def get_sentence_embedding_dimension(self) -> int:
        return self._dim

    def encode(self, texts, batch_size=32, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False):
        # Deterministic pseudo-embedding: hash-based, so identical text -> identical vector.
        vectors = []
        for text in texts:
            rng = np.random.default_rng(abs(hash(text)) % (2**32))
            vector = rng.random(self._dim).astype(np.float32)
            if normalize_embeddings:
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
            vectors.append(vector)
        return np.array(vectors, dtype=np.float32)


@pytest.fixture(autouse=True)
def _patch_sentence_transformer(monkeypatch):
    embedder_module._load_model.cache_clear()
    monkeypatch.setattr(embedder_module, "SentenceTransformer", _FakeSentenceTransformer)
    yield
    embedder_module._load_model.cache_clear()


def test_embed_texts_returns_correct_shape():
    embedder = embedder_module.Embedder(model_name="fake-model", device="cpu")
    vectors = embedder.embed_texts(["hello world", "another sentence"])

    assert vectors.shape == (2, embedder.dimension)
    assert vectors.dtype == np.float32


def test_embed_texts_empty_input_returns_empty_array():
    embedder = embedder_module.Embedder(model_name="fake-model", device="cpu")
    vectors = embedder.embed_texts([])
    assert vectors.shape == (0, embedder.dimension)


def test_embed_query_returns_single_vector():
    embedder = embedder_module.Embedder(model_name="fake-model", device="cpu")
    vector = embedder.embed_query("what helps with anxiety?")
    assert vector.shape == (embedder.dimension,)


def test_embed_chunks_preserves_content_and_metadata():
    embedder = embedder_module.Embedder(model_name="fake-model", device="cpu")
    metadata = ChunkMetadata(
        filename="a.txt",
        page=None,
        chunk_id="a-0-0-abc123",
        source="/tmp/a.txt",
        document_type=DocumentType.TXT,
    )
    chunks = [Chunk(content="breathing exercises help reduce stress", metadata=metadata)]

    embedded = embedder.embed_chunks(chunks)

    assert len(embedded) == 1
    assert embedded[0].content == chunks[0].content
    assert embedded[0].metadata == metadata
    assert len(embedded[0].embedding) == embedder.dimension
