from __future__ import annotations

import asyncio
import os
import tempfile

from gtts import gTTS
from telebot.async_telebot import AsyncTeleBot
from telebot import types

from .constants import OutputType
from .models import UserSettingsManager
from .bot import bot


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

async def _tts(text: str, lang: str) -> str:
    """Generate TTS MP3 via gTTS and return the temp-file path."""
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: gTTS(text, lang=lang).save(path))
    return path

# --------------------------------------------------------------------------- #
# Core voice sender                                                           #
# --------------------------------------------------------------------------- #

_original_send_message = AsyncTeleBot.send_message
_original_reply_to = AsyncTeleBot.reply_to


async def _send_voice(self: AsyncTeleBot, chat_id: int, text: str, **kw):
    """Send text or voice depending on the user’s preference."""
    async with UserSettingsManager(chat_id) as s:
        if not s.output_type == OutputType.VOICE:
            return await _original_send_message(self, chat_id, text, **kw)

        path = await _tts(text, str(s.language))
        try:
            kw.pop("parse_mode", None)  # Markdown in captions is unreliable
            with open(path, "rb") as f:
                res = await self.send_voice(chat_id, f, caption=text, **kw)
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
        return res


async def patched_send_message(self, chat_id, text, *a, **kw):  # type: ignore
    return await _send_voice(
        self,
        chat_id,
        text,
        *a,
        **kw
    )


async def patched_reply_to(self, msg: types.Message, text, *a, **kw):  # type: ignore
    return await _send_voice(
        self,
        msg.chat.id,
        text,
        reply_to_message_id=msg.message_id,
        *a,
        **kw,
    )


AsyncTeleBot.send_message = patched_send_message  # type: ignore
AsyncTeleBot.reply_to = patched_reply_to  # type: ignore


# --------------------------------------------------------------------------- #
# Patch edit_message_text (voice messages have no editable text field)        #
# --------------------------------------------------------------------------- #

_original_edit_message_text = AsyncTeleBot.edit_message_text


async def patched_edit_message_text(
    self,
    text: str,
    chat_id: int | None = None,
    message_id: int | None = None,
    inline_message_id: str | None = None,
    **kw,
):
    # Inline messages sent by other bots → leave untouched
    if inline_message_id is not None:
        return await _original_edit_message_text(
            self,
            text,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            **kw,
        )

    async with UserSettingsManager(chat_id) as s:
        if not s.output_type == OutputType.VOICE:
            # Normal text user → standard edit
            return await _original_edit_message_text(
                self, text, chat_id=chat_id, message_id=message_id, **kw
            )

    # Voice user → send a fresh audio message, then remove the old one
    has_buttons = "reply_markup" in kw
    reply_markup = kw.pop("reply_markup", None)
    sent = await _send_voice(self, chat_id, text, reply_markup=reply_markup)

    try:
        if has_buttons:
            async with bot as api:
                await bot.update_inline_buttons(chat_id, sent)
        else:
            await self.delete_message(chat_id, message_id)
    except Exception: # pylint: disable=broad-exception-caught
        pass

    return sent


AsyncTeleBot.edit_message_text = patched_edit_message_text  # type: ignore
