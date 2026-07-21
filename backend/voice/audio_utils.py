"""
Audio Utilities
Helper functions for audio file handling and format conversion.
"""

import os
import tempfile
import uuid
from typing import Optional
from fastapi import UploadFile
from backend.config import get_settings
from backend.utils.logger import voice_logger

settings = get_settings()

# Supported audio formats
SUPPORTED_FORMATS = {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac", ".mp4"}


def get_upload_dir() -> str:
    """Get or create the upload directory."""
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


async def save_upload_file(upload_file: UploadFile) -> str:
    """
    Save an uploaded audio file to disk.

    Args:
        upload_file: FastAPI UploadFile object

    Returns:
        Path to the saved file

    Raises:
        ValueError: If the file format is not supported
    """
    # Validate file extension
    filename = upload_file.filename or "audio.wav"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported audio format: {ext}. "
            f"Supported: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Generate unique filename
    unique_name = f"{uuid.uuid4()}{ext}"
    upload_dir = get_upload_dir()
    file_path = os.path.join(upload_dir, unique_name)

    # Save file
    voice_logger.info(f"Saving uploaded audio: {unique_name} ({upload_file.size or 'unknown'} bytes)")

    content = await upload_file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return file_path


def cleanup_file(file_path: str) -> None:
    """
    Remove a temporary file.

    Args:
        file_path: Path to the file to delete
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            voice_logger.info(f"Cleaned up: {file_path}")
    except OSError as e:
        voice_logger.warning(f"Failed to clean up {file_path}: {e}")


def get_audio_duration(file_path: str) -> Optional[float]:
    """
    Get the duration of an audio file in seconds.
    Requires pydub (which requires ffmpeg).

    Args:
        file_path: Path to the audio file

    Returns:
        Duration in seconds, or None if pydub is unavailable
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0  # pydub returns milliseconds
    except ImportError:
        voice_logger.warning("pydub not installed, skipping duration calculation")
        return None
    except Exception as e:
        voice_logger.warning(f"Could not get audio duration: {e}")
        return None


def convert_to_wav(input_path: str) -> str:
    """
    Convert an audio file to WAV format.
    Whisper works best with WAV files.

    Args:
        input_path: Path to the input audio file

    Returns:
        Path to the converted WAV file
    """
    if input_path.lower().endswith(".wav"):
        return input_path

    try:
        from pydub import AudioSegment

        voice_logger.info(f"Converting {input_path} to WAV")
        audio = AudioSegment.from_file(input_path)

        output_path = tempfile.mktemp(suffix=".wav")
        audio.export(output_path, format="wav")

        voice_logger.info(f"Converted to: {output_path}")
        return output_path

    except ImportError:
        voice_logger.warning("pydub not available, using original file")
        return input_path
