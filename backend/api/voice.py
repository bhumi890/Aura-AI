"""
Voice API Routes
Handles speech-to-text and text-to-speech operations.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_db
from backend.database.schema import TranscriptionResponse, SynthesisRequest
from backend.voice.speech_to_text import transcribe_audio
from backend.voice.text_to_speech import synthesize_speech
from backend.voice.audio_utils import (
    save_upload_file,
    cleanup_file,
    get_audio_duration,
    SUPPORTED_FORMATS,
)
from backend.utils.logger import voice_logger

router = APIRouter(prefix="/api/voice", tags=["Voice"])


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = "en",
):
    """
    Transcribe audio to text using Whisper.

    Accepts audio files in formats: WAV, MP3, M4A, OGG, WebM, FLAC, MP4.
    Returns the transcribed text along with detected language and duration.

    This is the main Speech-to-Text (STT) endpoint.
    The frontend Voice component sends recorded audio here.
    """
    voice_logger.info(f"Transcription request: {audio.filename}, lang={language}")

    # Save uploaded file
    try:
        audio_path = await save_upload_file(audio)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        # Get duration (optional)
        duration = get_audio_duration(audio_path)

        # Transcribe
        result = await transcribe_audio(audio_path, language=language)

        return TranscriptionResponse(
            text=result["text"],
            language=result.get("language", language),
            duration=duration,
        )

    except Exception as e:
        voice_logger.error(f"Transcription failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )
    finally:
        # Clean up uploaded file
        cleanup_file(audio_path)


@router.post("/synthesize")
async def synthesize(request: SynthesisRequest):
    """
    Convert text to speech audio.

    Returns an MP3 audio file that the frontend can play.
    This is the main Text-to-Speech (TTS) endpoint.
    """
    voice_logger.info(f"Synthesis request: {len(request.text)} chars, lang={request.language}")

    try:
        # Generate speech
        audio_path = await synthesize_speech(
            text=request.text,
            language=request.language,
        )

        # Return audio file
        return FileResponse(
            path=audio_path,
            media_type="audio/mpeg",
            filename="response.mp3",
            background=None,  # File will be cleaned up manually
        )

    except Exception as e:
        voice_logger.error(f"Synthesis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Speech synthesis failed: {str(e)}"
        )


@router.get("/formats")
async def supported_formats():
    """Get list of supported audio formats for transcription."""
    return {
        "supported_formats": list(SUPPORTED_FORMATS),
        "max_file_size_mb": 25,
    }
