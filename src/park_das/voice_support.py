"""
Voice support module for the park-das Telegram bot.

This module provides functionality to convert incoming voice messages into text
using the Whisper speech recognition model. It processes voice messages and forwards
the transcribed text to the existing free_text_handler, allowing users to interact
with the bot using voice commands instead of typing.

The module implements:
- Lazy initialization of the Whisper model to optimize startup time
- Asynchronous audio conversion from OGG (Telegram format) to WAV
- Speech-to-text transcription via Whisper AI

Note: All previous keyword routing functions have been removed as this module
only performs speech-to-text conversion.
"""

import os
import asyncio
import logging
import tempfile
from pathlib import Path

import whisper
from telebot import types

from .bot import bot

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Whisper Initialization
# ---------------------------------------------------------------------------

# Model size can be configured via environment variable or defaults to 'tiny'
# Available sizes: tiny, base, small, medium, large
_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "tiny")

# The model is initialized lazily on first use to prevent long startup times
_whisper_model: whisper.Whisper | None = None # pylint: disable=invalid-name

def _whisper() -> whisper.Whisper:
    """
    Lazily loads the Whisper model to prevent long startup times.

    The function ensures the model is only loaded once and then reused for subsequent calls.
    The model size is determined by the WHISPER_MODEL_SIZE environment variable.

    :return: Initialized Whisper model instance
    """
    global _whisper_model  # pylint: disable=global-statement
    if _whisper_model is None:
        logger.info("Loading Whisper model '%s'...", _MODEL_SIZE)
        _whisper_model = whisper.load_model(_MODEL_SIZE)
    return _whisper_model


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

async def _ogg_to_wav(ogg_path: str) -> str:
    """
    Converts an OGG audio file to WAV format asynchronously using ffmpeg.

    Telegram voice messages are in OGG format, but Whisper requires WAV.
    This function handles the conversion by running ffmpeg in a separate process.

    :param ogg_path: Path to the source OGG file
    :return: Path to the converted WAV file
    """
    loop = asyncio.get_running_loop()
    wav_path = Path(tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name)

    # Run ffmpeg in a separate thread to avoid blocking the event loop
    # Convert to 16kHz mono WAV format which works best with Whisper
    await loop.run_in_executor(
        None,
        lambda: os.system(
            f"ffmpeg -y -i '{ogg_path}' -ar 16000 -ac 1 '{wav_path}' \
               >/dev/null 2>&1"
        ),
    )
    return str(wav_path)


# ---------------------------------------------------------------------------
# Main Handler
# ---------------------------------------------------------------------------

async def transcripe(message: types.Message) -> str | None:
    """
    Processes incoming voice messages and transcribes them to text.

    This function:
    1. Downloads the voice message from Telegram
    2. Saves it as a temporary OGG file
    3. Converts it to WAV format
    4. Transcribes the audio using Whisper
    5. Cleans up temporary files

    :param message: Telegram message object containing a voice message
    :return: Transcribed text or None if transcription failed
    """
    # Download the voice message from Telegram servers
    async with bot as api:
        file_info = await api.get_file(message.voice.file_id)  # type: ignore
        ogg_bytes = await api.download_file(file_info.file_path)

    # Save the downloaded bytes to a temporary OGG file
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp.write(ogg_bytes)
        ogg_path = tmp.name

    # Convert OGG to WAV format and clean up the OGG file
    try:
        wav_path = await _ogg_to_wav(ogg_path)
    finally:
        Path(ogg_path).unlink(missing_ok=True)  # Delete temporary OGG file

    # Run transcription in a thread pool to avoid blocking the event loop
    # Whisper operations are CPU-intensive and can take some time
    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(
            None,
            lambda: _whisper().transcribe(
                wav_path,
                language=None,  # Automatic language detection
                fp16=False      # Don't use float16 precision (more compatible)
            )
        )
        return result.get("text", "").strip()  # type: ignore
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Transcription failed")
        return None
    finally:
        Path(wav_path).unlink(missing_ok=True)  # Delete temporary WAV file
