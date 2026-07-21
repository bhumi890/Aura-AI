"""
FAISS vector store.

Wraps a FAISS `IndexFlatIP` (cosine similarity via normalized inner product)
with disk persistence. If a persisted index already exists on disk, it is
loaded automatically; otherwise a fresh index is created on first use.
"""

from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

from ai_core.rag.config import settings
from ai_core.rag.logging_utils import get_logger
from ai_core.rag.models import ChunkMetadata, EmbeddedChunk

logger = get_logger(__name__)

_INDEX_FILENAME = "index.faiss"
_METADATA_FILENAME = "metadata.json"


class FaissStore:
    """Persistent FAISS-backed vector store for embedded chunks."""

    def __init__(self, store_dir: Path | None = None, dimension: int | None = None) -> None:
        self.store_dir = store_dir or settings.vector_db_path
        self.store_dir.mkdir(parents=True, exist_ok=True)

        self._index_path = self.store_dir / _INDEX_FILENAME
        self._metadata_path = self.store_dir / _METADATA_FILENAME

        self._dimension = dimension
        self._index: faiss.Index | None = None
        # Maps FAISS internal row id -> (content, metadata dict)
        self._records: list[dict] = []

        self._load_or_initialize()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def _load_or_initialize(self) -> None:
        if self._index_path.exists() and self._metadata_path.exists():
            logger.info("Existing FAISS index found at %s — reloading", self._index_path)
            self._index = faiss.read_index(str(self._index_path))
            self._records = json.loads(self._metadata_path.read_text(encoding="utf-8"))
            self._dimension = self._index.d
        elif self._dimension is not None:
            logger.info("No existing FAISS index found — initializing a new one (dim=%d)", self._dimension)
            self._index = faiss.IndexFlatIP(self._dimension)
            self._records = []
        else:
            logger.info("No existing FAISS index found and no dimension provided — deferring initialization")
            self._index = None
            self._records = []

    def _ensure_initialized(self, dimension: int) -> None:
        if self._index is None:
            self._dimension = dimension
            self._index = faiss.IndexFlatIP(dimension)
            self._records = []
        elif self._index.d != dimension:
            raise ValueError(
                f"Embedding dimension mismatch: store expects {self._index.d}, got {dimension}"
            )

    def save(self) -> None:
        if self._index is None:
            logger.warning("Attempted to save an uninitialized FAISS index — skipping")
            return
        faiss.write_index(self._index, str(self._index_path))
        self._metadata_path.write_text(json.dumps(self._records), encoding="utf-8")
        logger.info("Persisted FAISS index (%d vectors) to %s", self._index.ntotal, self.store_dir)

    def clear(self) -> None:
        """Delete the persisted index/metadata and reset in-memory state."""
        for path in (self._index_path, self._metadata_path):
            if path.exists():
                path.unlink()
        self._index = None
        self._records = []
        logger.info("Cleared FAISS store at %s", self.store_dir)

    # ------------------------------------------------------------------ #
    # Mutation
    # ------------------------------------------------------------------ #
    def add(self, embedded_chunks: list[EmbeddedChunk]) -> None:
        if not embedded_chunks:
            return

        dimension = len(embedded_chunks[0].embedding)
        self._ensure_initialized(dimension)
        assert self._index is not None

        vectors = np.array([chunk.embedding for chunk in embedded_chunks], dtype=np.float32)
        self._index.add(vectors)
        self._records.extend(
            {"content": chunk.content, "metadata": chunk.metadata.as_dict()}
            for chunk in embedded_chunks
        )
        logger.info("Added %d vector(s) to FAISS store (total=%d)", len(embedded_chunks), self._index.ntotal)

    # ------------------------------------------------------------------ #
    # Query
    # ------------------------------------------------------------------ #
    def search(self, query_vector: np.ndarray, top_k: int) -> list[tuple[str, ChunkMetadata, float]]:
        """
        Search the index for the top_k nearest neighbours of `query_vector`.

        Returns a list of (content, metadata, similarity_score) tuples,
        ordered by descending similarity.
        """
        if self._index is None or self._index.ntotal == 0:
            logger.warning("Search attempted on an empty FAISS index")
            return []

        query = np.asarray(query_vector, dtype=np.float32).reshape(1, -1)
        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(query, k)

        results: list[tuple[str, ChunkMetadata, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            record = self._records[idx]
            results.append((record["content"], ChunkMetadata(**record["metadata"]), float(score)))

        return results

    @property
    def size(self) -> int:
        return self._index.ntotal if self._index is not None else 0
