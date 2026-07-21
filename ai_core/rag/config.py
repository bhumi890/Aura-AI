"""
Centralized configuration for the RAG pipeline.

All configurable values are read from environment variables (via a .env
file). Nothing is hardcoded, per project guidelines. This module is the
single source of truth for configuration and should be imported wherever
configurable values are needed.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration, populated from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Paths -----------------------------------------------------------
    documents_dir: str = Field(default="rag/documents", alias="DOCUMENTS_DIR")
    vector_db_dir: str = Field(default="rag/vectordb/store", alias="VECTOR_DB_DIR")
    log_dir: str = Field(default="logs", alias="LOG_DIR")

    # --- Embedding model ---------------------------------------------------
    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL_NAME",
    )
    embedding_device: str = Field(default="cpu", alias="EMBEDDING_DEVICE")
    embedding_batch_size: int = Field(default=32, alias="EMBEDDING_BATCH_SIZE")

    # --- Chunking ----------------------------------------------------------
    chunk_size: int = Field(default=500, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, alias="CHUNK_OVERLAP")

    # --- Retrieval -----------------------------------------------------
    top_k: int = Field(default=5, alias="TOP_K")

    # --- Supported document types -------------------------------------
    supported_extensions: tuple[str, ...] = (".pdf", ".txt", ".md", ".docx")

    # --- Logging -------------------------------------------------------
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def documents_path(self) -> Path:
        return Path(self.documents_dir)

    @property
    def vector_db_path(self) -> Path:
        return Path(self.vector_db_dir)

    @property
    def log_path(self) -> Path:
        return Path(self.log_dir)


settings = Settings()
