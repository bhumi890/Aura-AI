"""
Embedding generation.

Wraps `sentence-transformers/all-MiniLM-L6-v2` (configurable via .env) to
convert chunk text into dense vectors for FAISS indexing and query-time
similarity search.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from ai_core.rag.config import settings
from ai_core.rag.logging_utils import get_logger
from ai_core.rag.models import Chunk, EmbeddedChunk

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _load_model(model_name: str, device: str):
    """Load (and cache) the SentenceTransformer model. Loading is expensive."""
    from sentence_transformers import SentenceTransformer
    logger.info("Loading embedding model '%s' on device '%s'", model_name, device)
    return SentenceTransformer(model_name, device=device)


class Embedder:
    """Thin, testable wrapper around a SentenceTransformer embedding model."""

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        batch_size: int | None = None,
    ) -> None:
        self.model_name = model_name or settings.embedding_model_name
        self.device = device or settings.embedding_device
        self.batch_size = batch_size or settings.embedding_batch_size
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._model = _load_model(self.model_name, self.device)
        return self._model

    @property
    def dimension(self) -> int:
        return int(self.model.get_sentence_embedding_dimension())

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of raw strings, returning an (N, dim) float32 array."""
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query string, returning a (dim,) float32 vector."""
        return self.embed_texts([query])[0]

    def embed_chunks(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        """Embed a list of Chunk objects, returning EmbeddedChunk objects."""
        if not chunks:
            return []

        vectors = self.embed_texts([chunk.content for chunk in chunks])
        embedded = [
            EmbeddedChunk(
                content=chunk.content,
                metadata=chunk.metadata,
                embedding=vector.tolist(),
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        logger.info("Generated embeddings for %d chunk(s)", len(embedded))
        return embedded
