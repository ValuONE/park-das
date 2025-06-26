from __future__ import annotations

import asyncio
import os
import re
import tempfile

from gtts import gTTS
from telebot.async_telebot import AsyncTeleBot
from telebot import types

import i18n

from .constants import OutputType
from .models import UserSettingsManager
from .bot import bot

# --------------------------------------------------------------------------- #
# Emoji handling                                                              #
# --------------------------------------------------------------------------- #

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Symbols & pictograms
    "\U0001F680-\U0001F6FF"  # Transport & Maps
    "\U0001F700-\U0001F77F"  # Alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric shapes
    "\U0001F800-\U0001F8FF"  # Additional arrows
    "\U0001F900-\U0001F9FF"  # Additional icons
    "\U0001FA00-\U0001FA6F"  # Advanced icons
    "\U0001FA70-\U0001FAFF"  # More advanced icons ^^
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"  # Various general symbols
    "]+",
    flags=re.UNICODE,
)

def remove_emojis(text: str) -> str:
    """Remove *all* emoji glyphs from *text* (for clean TTS)."""
    return EMOJI_PATTERN.sub("", text)


# --------------------------------------------------------------------------- #
# TTS helper                                                                  #
# --------------------------------------------------------------------------- #

async def _tts(text: str, lang: str) -> str:
    """Generate an MP3 via gTTS and return the temp-file path."""
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: gTTS(text, lang=lang).save(path))
    return path


# --------------------------------------------------------------------------- #
# Monkey-patch TeleBot                                                        #
# --------------------------------------------------------------------------- #

_original_send_message = AsyncTeleBot.send_message
_original_reply_to = AsyncTeleBot.reply_to
_original_edit_message_text = AsyncTeleBot.edit_message_text


async def _send_voice(self: AsyncTeleBot, chat_id: int, text: str, **kw):
    """Route a message either as plain text or voiced audio depending on the
    user preference; provides UX niceties for TTS generation.

    UX details (PA-01 & PA-02):
    • For *speech output* users*, a placeholder
    "Generating voice message..." is sent immediately (with *original* send_message to
    prevent recursion).
    • Once the MP3 is ready, the placeholder is deleted.
    • Emojis are removed only for the *spoken* version, so they remain
    visible in the chat but are not read aloud.
    """

    async with UserSettingsManager(chat_id) as s:
        # ------------------------------------------------------------------
        # TEXT-only users
        # ------------------------------------------------------------------
        if s.output_type != OutputType.VOICE:
            return await _original_send_message(self, chat_id, text, **kw)

        # ------------------------------------------------------------------
        # VOICE users → first generate TTS message then TTS output itself
        # ------------------------------------------------------------------
        locale = str(s.language)
        placeholder_msg = await _original_send_message(
            self,
            chat_id,
            i18n.t("strings.voice.processing", locale),
            reply_to_message_id=kw.get("reply_to_message_id"),
        )

        spoken_text = remove_emojis(text)
        path = await _tts(spoken_text, locale)
        try:
            kw.pop("parse_mode", None)
            with open(path, "rb") as fh:
                voice_msg = await self.send_voice(
                    chat_id,
                    fh,
                    caption=text,  # original message (incl. Emojis)
                    **kw,
                )
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

        # Remove placeholder message
        try:
            await self.delete_message(chat_id, placeholder_msg.message_id)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        return voice_msg


async def patched_send_message(self, chat_id, text, *a, **kw):  # type: ignore
    return await _send_voice(self, chat_id, text, *a, **kw)


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


# ---------------------------------------------------------------------------
# Patch edit_message_text (Voice messages do not have editable text)
# ---------------------------------------------------------------------------

async def patched_edit_message_text(
        self,
        text: str,
        chat_id: int | None = None,
        message_id: int | None = None,
        inline_message_id: str | None = None,
        **kw,
):
    # Inline-messages of other Bots → do not touch them
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
        if s.output_type != OutputType.VOICE:
            return await _original_edit_message_text(
                self, text, chat_id=chat_id, message_id=message_id, **kw
            )

    # Voice-User: send new voice message, delete old one
    has_buttons = "reply_markup" in kw
    reply_markup = kw.pop("reply_markup", None)
    sent = await _send_voice(self, chat_id, text, reply_markup=reply_markup)

    try:
        if has_buttons:
            await bot.update_inline_buttons(chat_id, sent)
        else:
            await self.delete_message(chat_id, message_id)
    except Exception:  # pylint: disable=broad-exception-caught
        pass

    return sent

AsyncTeleBot.edit_message_text = patched_edit_message_text  # type: ignore
