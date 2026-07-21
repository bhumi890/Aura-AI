"""
Backend Configuration
Loads settings from .env file using pydantic-settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./wellness_companion.db",
        description="Database connection string"
    )

    # ── OpenAI ────────────────────────────────────────────────
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key for Whisper API and optional LLM"
    )

    # ── Voice Settings ────────────────────────────────────────
    WHISPER_MODE: str = Field(
        default="local",
        description="'local' for local Whisper model, 'api' for OpenAI API"
    )
    WHISPER_MODEL: str = Field(
        default="base",
        description="Whisper model size: tiny, base, small, medium, large"
    )
    TTS_PROVIDER: str = Field(
        default="gtts",
        description="TTS provider: 'gtts' or 'openai'"
    )

    # ── Server ────────────────────────────────────────────────
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    DEBUG: bool = Field(default=True)

    # ── CORS ──────────────────────────────────────────────────
    FRONTEND_URL: str = Field(
        default="http://localhost:5173",
        description="Frontend URL for CORS"
    )

    # ── Auth ──────────────────────────────────────────────────
    API_SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT/session auth"
    )

    # ── Paths ─────────────────────────────────────────────────
    UPLOAD_DIR: str = Field(
        default="uploads",
        description="Directory for temporary audio uploads"
    )

    # ── AI Core (Groq / LangGraph / RAG) ─────────────────────
    GROQ_API_KEY: str = Field(default="", description="Groq API key 1")
    GROQ_API_KEY_2: str = Field(default="", description="Groq API key 2")
    GROQ_API_KEY_3: str = Field(default="", description="Groq API key 3")
    GROQ_API_KEY_4: str = Field(default="", description="Groq API key 4")
    HOMEMIND_ENV: str = Field(default="development")
    SQLITE_DB_PATH: str = Field(default="homemind_dev.db")
    SUMMARIZE_TRIGGER_TURNS: int = Field(default=8)
    DOCUMENTS_DIR: str = Field(default="ai_core/rag/documents")
    VECTOR_DB_DIR: str = Field(default="ai_core/rag/vectordb/store")
    EMBEDDING_MODEL_NAME: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DEVICE: str = Field(default="cpu")
    TOP_K: int = Field(default=5)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings instance.
    Uses lru_cache so .env is read only once.
    """
    s = Settings()
    if s.GROQ_API_KEY:
        os.environ["GROQ_API_KEY"] = s.GROQ_API_KEY
    if s.GROQ_API_KEY_2:
        os.environ["GROQ_API_KEY_2"] = s.GROQ_API_KEY_2
    if s.GROQ_API_KEY_3:
        os.environ["GROQ_API_KEY_3"] = s.GROQ_API_KEY_3
    if s.GROQ_API_KEY_4:
        os.environ["GROQ_API_KEY_4"] = s.GROQ_API_KEY_4
    return s
