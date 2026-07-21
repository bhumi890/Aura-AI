"""
Speech to Text
Whisper integration with support for both local model and OpenAI API.
"""

import os
import tempfile
from typing import Optional
from backend.config import get_settings
from backend.utils.logger import voice_logger

settings = get_settings()

# ── Local Whisper Model (lazy loaded) ─────────────────────────
_whisper_model = None


def _get_local_model():
    """Lazy-load the local Whisper model."""
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            voice_logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL}")
            _whisper_model = whisper.load_model(settings.WHISPER_MODEL)
            voice_logger.info("Whisper model loaded successfully")
        except ImportError:
            voice_logger.error(
                "openai-whisper package not installed. "
                "Install with: pip install openai-whisper"
            )
            raise
    return _whisper_model


async def transcribe_audio(
    audio_path: str,
    language: Optional[str] = None,
) -> dict:
    """
    Transcribe audio file to text.

    Args:
        audio_path: Path to the audio file
        language: Optional language code (e.g., 'en', 'hi')

    Returns:
        dict with keys: text, language, duration
    """
    if settings.WHISPER_MODE == "api":
        return await _transcribe_via_api(audio_path, language)
    else:
        return await _transcribe_locally(audio_path, language)


async def _transcribe_locally(
    audio_path: str,
    language: Optional[str] = None,
) -> dict:
    """Transcribe using local Whisper model."""
    import asyncio

    voice_logger.info(f"Transcribing locally: {audio_path}")

    def _run_transcription():
        model = _get_local_model()
        options = {}
        if language:
            options["language"] = language

        result = model.transcribe(audio_path, **options)
        return {
            "text": result["text"].strip(),
            "language": result.get("language", language or "en"),
            "duration": None,  # Whisper doesn't directly return duration
        }

    # Run CPU-bound transcription in thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_transcription)

    voice_logger.info(f"Transcription complete: {len(result['text'])} chars")
    return result


async def _transcribe_via_api(
    audio_path: str,
    language: Optional[str] = None,
) -> dict:
    """Transcribe using OpenAI Whisper API."""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        voice_logger.error("openai package not installed. Install with: pip install openai")
        raise

    voice_logger.info(f"Transcribing via OpenAI API: {audio_path}")

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    with open(audio_path, "rb") as audio_file:
        kwargs = {"model": "whisper-1", "file": audio_file}
        if language:
            kwargs["language"] = language

        transcript = await client.audio.transcriptions.create(**kwargs)

    result = {
        "text": transcript.text.strip(),
        "language": language or "en",
        "duration": None,
    }

    voice_logger.info(f"API transcription complete: {len(result['text'])} chars")
    return result
