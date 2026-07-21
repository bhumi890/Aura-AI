"""
Text to Speech
TTS integration with support for gTTS and OpenAI TTS.
"""

import os
import tempfile
import asyncio
from typing import Optional
from backend.config import get_settings
from backend.utils.logger import voice_logger

settings = get_settings()


async def synthesize_speech(
    text: str,
    language: str = "en",
    output_path: Optional[str] = None,
) -> str:
    """
    Convert text to speech audio file.

    Args:
        text: Text to convert to speech
        language: Language code (default: 'en')
        output_path: Optional output path. If None, creates a temp file.

    Returns:
        Path to the generated audio file (MP3)
    """
    if settings.TTS_PROVIDER == "openai":
        return await _synthesize_openai(text, output_path)
    else:
        return await _synthesize_gtts(text, language, output_path)


async def _synthesize_gtts(
    text: str,
    language: str = "en",
    output_path: Optional[str] = None,
) -> str:
    """Generate speech using Google TTS (free, no API key needed)."""
    try:
        from gtts import gTTS
    except ImportError:
        voice_logger.error("gTTS not installed. Install with: pip install gTTS")
        raise

    voice_logger.info(f"Synthesizing with gTTS: {len(text)} chars, lang={language}")

    if not output_path:
        fd, output_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)

    def _generate():
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(output_path)
        return output_path

    # gTTS does network I/O, run in executor
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _generate)

    voice_logger.info(f"gTTS audio saved to: {result}")
    return result


async def _synthesize_openai(
    text: str,
    output_path: Optional[str] = None,
) -> str:
    """Generate speech using OpenAI TTS API."""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        voice_logger.error("openai package not installed. Install with: pip install openai")
        raise

    voice_logger.info(f"Synthesizing with OpenAI TTS: {len(text)} chars")

    if not output_path:
        fd, output_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    response = await client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )

    # Write the audio content to file
    with open(output_path, "wb") as f:
        async for chunk in response.iter_bytes():
            f.write(chunk)

    voice_logger.info(f"OpenAI TTS audio saved to: {output_path}")
    return output_path
