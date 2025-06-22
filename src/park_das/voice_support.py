"""
support for the park-das Telegram bot.

Converts incoming voice messages into text using Whisper and forwards
them to the existing free_text_handler, so that the already
implemented command logic for text messages is used unchanged.

All previous keyword routing functions have been removed - this module only performs speech-to-text.
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile

from pathlib import Path

import whisper
from telebot import formatting, types
from telebot.async_telebot import AsyncTeleBot
from telebot.states.sync import StateContext

import i18n

from .bot import bot
from .handlers import free_text_handler
from .models import UserSettingsManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Whisper‑Initialization
# ---------------------------------------------------------------------------
_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "tiny")
_whisper_model: whisper.Whisper | None = None

def _whisper() -> whisper.Whisper:
    """Lazy‑load of the Whisper-Model to prevent long startup times."""

    global _whisper_model  # pylint: disable=global-statement
    if _whisper_model is None:
        logger.info("Lade Whisper‑Modell '%s'…", _MODEL_SIZE)
        _whisper_model = whisper.load_model(_MODEL_SIZE)
    return _whisper_model


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

async def _ogg_to_wav(ogg_path: str) -> str:
    """OGG-file asynchronously to WAVE using ffmpeg."""

    loop = asyncio.get_running_loop()
    wav_path = Path(tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name)
    await loop.run_in_executor(
        None,
        lambda: os.system(
            f"ffmpeg -y -i '{ogg_path}' -ar 16000 -ac 1 '{wav_path}' \
               >/dev/null 2>&1"
        ),
    )
    return str(wav_path)


# ---------------------------------------------------------------------------
# Haupt‑Handler
# ---------------------------------------------------------------------------

async def _voice_handler(message: types.Message, state: StateContext):
    """Process incoming voice messages."""

    chat_id = message.chat.id

    # Download the voice message
    async with bot as api:
        file_info = await api.get_file(message.voice.file_id)
        ogg_bytes = await api.download_file(file_info.file_path)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp.write(ogg_bytes)
        ogg_path = tmp.name

    # Convert OGG to WAV
    try:
        wav_path = await _ogg_to_wav(ogg_path)
    finally:
        Path(ogg_path).unlink(missing_ok=True)

    # Transcribe (blocking -> thread pool)
    loop = asyncio.get_running_loop()
    try:
        async with UserSettingsManager(message.from_user) as settings:
            try:
                result = await loop.run_in_executor(
                    None,
                    lambda: _whisper().transcribe(wav_path, language=None)
                )
                text: str = result.get("text", "").strip()

            except Exception: # pylint: disable=broad-exception-caught
                logger.exception("Transcription failed")
                text = ""
    finally:
        Path(wav_path).unlink(missing_ok=True)


    if not text:
        await bot.api.send_message(
            chat_id,
            i18n.t("voice.not_understood", str(settings.language))
        )
        return

    # Echo so the user knows what was transcribed
    await bot.api.send_message(
        chat_id,
        formatting.escape_markdown(f"*{text}*"),
        parse_mode="Markdown",
    )

    message.text = text
    await free_text_handler(message, state)

def register_voice_handler(bot_instance: AsyncTeleBot | None = None):
    (bot_instance or bot).api.message_handler(content_types=["voice"])(_voice_handler)
    logger.info("Voice handler registered.")

# Registrate voice handler on module import
register_voice_handler()
