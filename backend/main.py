"""
AI Emotional Wellness Companion — Backend
==========================================
FastAPI application entry point.

Member 4 (SHEEL) — Backend + Voice + Database

Start the server:
    uvicorn backend.main:app --reload

API Documentation:
    http://localhost:8000/docs (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

import os

# Limit thread memory allocations for Render free tier (512MB RAM limit)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.database.connection import create_tables
from backend.utils.logger import logger

# AI Core (LangGraph pipeline)
from ai_core.runtime import build_app as build_ai_app
from ai_core.graph.checkpointer import close_checkpointers

# ── API Routers ───────────────────────────────────────────────
from backend.api.chat import router as chat_router
from backend.api.journal import router as journal_router
from backend.api.mood import router as mood_router
from backend.api.wellness import router as wellness_router
from backend.api.history import router as history_router
from backend.api.users import router as users_router
from backend.api.rag import router as rag_router



# Voice router is optional — depends on whisper/gTTS which may not be installed
try:
    from backend.api.voice import router as voice_router
    _voice_available = True
except ImportError as e:
    logger.warning(f"Voice module not available (missing dependency): {e}")
    voice_router = None
    _voice_available = False

settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    - On startup: Create database tables, create upload directory
    - On shutdown: Cleanup resources
    """
    logger.info("🚀 Starting AI Emotional Wellness Companion Backend...")

    # Create database tables
    await create_tables()
    logger.info("✅ Database tables created")

    # Create upload directory for voice files
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"✅ Upload directory ready: {settings.UPLOAD_DIR}")

    # Build AI pipeline (LangGraph)
    try:
        app.state.ai_app = await build_ai_app()
        logger.info("✅ AI pipeline compiled (LangGraph + Gemini)")
    except Exception as e:
        logger.error(f"⚠️ AI pipeline failed to compile: {e}")
        logger.warning("Chat endpoint will return fallback responses until AI is available")
        app.state.ai_app = None

    logger.info(f"✅ Server running on {settings.HOST}:{settings.PORT}")
    logger.info(f"📖 API Docs: http://localhost:{settings.PORT}/docs")

    yield  # Application is running

    # Shutdown — close checkpointer connections
    try:
        await close_checkpointers()
        logger.info("✅ AI checkpointer connections closed")
    except Exception as e:
        logger.error(f"⚠️ Error closing checkpointers: {e}")
    logger.info("👋 Shutting down...")


# ── FastAPI App ───────────────────────────────────────────────
app = FastAPI(
    title="AI Emotional Wellness Companion",
    description=(
        "Backend API for the AI Emotional Wellness Companion. "
        "Provides chat, journal, mood tracking, voice interaction, "
        "and wellness plan management."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ── CORS ──────────────────────────────────────────────────────
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
]

# Add production frontend URL from environment if set
if settings.FRONTEND_URL and settings.FRONTEND_URL not in allowed_origins:
    allowed_origins.append(settings.FRONTEND_URL)

# Also allow *.onrender.com for Render preview URLs
allowed_origins_regex = r"https://.*\.onrender\.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allowed_origins_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register Routers ─────────────────────────────────────────
app.include_router(users_router)
app.include_router(chat_router)

app.include_router(journal_router)
app.include_router(mood_router)
if _voice_available:
    app.include_router(voice_router)
app.include_router(wellness_router)
app.include_router(history_router)
app.include_router(rag_router)



# ── Health Check ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Emotional Wellness Companion",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "voice": {
            "whisper_mode": settings.WHISPER_MODE,
            "tts_provider": settings.TTS_PROVIDER,
        },
    }


# ── Run directly ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
