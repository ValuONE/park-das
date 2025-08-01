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
from .models import UserManager
from .bot import bot

# --------------------------------------------------------------------------- #
# Emoji handling                                                              #
# --------------------------------------------------------------------------- #

# Regex pattern to match and remove all emoji characters from text.
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
    """
    Removes all emoji glyphs from the given text.

    :param text: The input text containing emojis.
    :return: The text with all emojis removed.
    """
    return EMOJI_PATTERN.sub("", text)


# --------------------------------------------------------------------------- #
# TTS helper                                                                  #
# --------------------------------------------------------------------------- #

async def _tts(text: str, lang: str) -> str:
    """
    Generates a temporary MP3 file from the given text using gTTS.

    :param text: The text to convert to speech.
    :param lang: The language code for the TTS (e.g., 'en', 'de').
    :return: The path to the generated MP3 file.
    """
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: gTTS(text, lang=lang).save(path))
    return path


# --------------------------------------------------------------------------- #
# Monkey-patch TeleBot                                                        #
# --------------------------------------------------------------------------- #

# Backup of the original methods to allow patching.
_original_send_message = AsyncTeleBot.send_message
_original_reply_to = AsyncTeleBot.reply_to
_original_edit_message_text = AsyncTeleBot.edit_message_text

async def _send_voice(self: AsyncTeleBot, chat_id: int, text: str, **kw):
    """
    Sends a message as either plain text or a voice message based on user preferences.

    - For users with voice output enabled, a placeholder message is sent while
        the TTS is being generated.
    - Emojis are removed from the spoken version but remain in the text message.
    - The placeholder is deleted once the voice message is sent.

    :param self: The AsyncTeleBot instance.
    :param chat_id: The ID of the chat to send the message to.
    :param text: The text to send or convert to speech.
    :param kw: Additional keyword arguments for the message.
    :return: The sent message object.
    """
    voice_only: bool = kw.pop("voice_only", False)

    async with UserManager(chat_id) as s:
        # Handle text-only users
        if s.output_type != OutputType.VOICE:
            return await _original_send_message(self, chat_id, text, **kw)

        # Handle voice output users
        locale = str(s.language)
        placeholder_msg = await _original_send_message(
            self,
            chat_id,
            i18n.t("voice.processing", locale),
            reply_to_message_id=kw.get("reply_to_message_id"),
        )

        spoken_text = remove_emojis(text)
        path = await _tts(spoken_text, locale)
        try:
            kw.pop("parse_mode", None)

            with open(path, "rb") as fh:
                if voice_only:
                    voice_msg = await self.send_voice(chat_id, fh, **kw)
                else:
                    voice_msg = await self.send_voice(
                        chat_id,
                        fh,
                        caption=text,  # Original message (including emojis)
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
        except Exception:  # Broad exception handling for cleanup
            pass

        return voice_msg


async def patched_send_message(self, chat_id, text, *a, **kw):  # type: ignore
    """
    Patched version of send_message to support voice output.

    :param self: The AsyncTeleBot instance.
    :param chat_id: The ID of the chat to send the message to.
    :param text: The text to send or convert to speech.
    :param a: Additional positional arguments.
    :param kw: Additional keyword arguments.
    :return: The sent message object.
    """
    return await _send_voice(self, chat_id, text, *a, **kw)


async def patched_reply_to(self, msg: types.Message, text, *a, **kw):  # type: ignore
    """
    Patched version of reply_to to support voice output.

    :param self: The AsyncTeleBot instance.
    :param msg: The message to reply to.
    :param text: The text to send or convert to speech.
    :param a: Additional positional arguments.
    :param kw: Additional keyword arguments.
    :return: The sent message object.
    """
    return await _send_voice(
        self,
        msg.chat.id,
        text,
        reply_to_message_id=msg.message_id,
        *a,
        **kw,
    )


# Apply the patched methods to the AsyncTeleBot class.
AsyncTeleBot.send_message = patched_send_message  # type: ignore
AsyncTeleBot.reply_to = patched_reply_to  # type: ignore


# --------------------------------------------------------------------------- #
# Patch edit_message_text (Voice messages do not have editable text)          #
# --------------------------------------------------------------------------- #

async def patched_edit_message_text(
        self,
        text: str,
        chat_id: int | None = None,
        message_id: int | None = None,
        inline_message_id: str | None = None,
        **kw,
):
    """
    Patched version of edit_message_text to support voice output.

    - For voice users, a new voice message is sent instead of editing the text.
    - The old message is deleted after the new one is sent.

    :param self: The AsyncTeleBot instance.
    :param text: The new text to send or convert to speech.
    :param chat_id: The ID of the chat containing the message.
    :param message_id: The ID of the message to edit.
    :param inline_message_id: The ID of the inline message to edit (if any).
    :param kw: Additional keyword arguments.
    :return: The sent message object.
    """
    # Inline messages sent by other bots are not modified.
    if inline_message_id is not None:
        return await _original_edit_message_text(
            self,
            text,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            **kw,
        )

    async with UserManager(chat_id) as s:
        if s.output_type != OutputType.VOICE:
            return await _original_edit_message_text(
                self, text, chat_id=chat_id, message_id=message_id, **kw
            )

    # For voice users, send a new voice message and delete the old one.
    has_buttons = "reply_markup" in kw
    reply_markup = kw.pop("reply_markup", None)
    sent = await _send_voice(self, chat_id, text, reply_markup=reply_markup) # type: ignore

    try:
        if has_buttons:
            await bot.update_inline_buttons(chat_id, sent) # type: ignore
        else:
            await self.delete_message(chat_id, message_id)
    except Exception:  # Broad exception handling for cleanup
        pass

    return sent

# Apply the patched edit_message_text method to the AsyncTeleBot class.
AsyncTeleBot.edit_message_text = patched_edit_message_text  # type: ignore

# Backup of the original send_photo method.
_original_send_photo = AsyncTeleBot.send_photo

async def patched_send_photo(self, chat_id: int, photo, *a, **kw):  # type: ignore
    """
    Patched version of send_photo to support voice output.

    - For voice users, a voice message with the caption is sent before the photo.
    - The sequence ensures the voice message appears above the image.

    :param self: The AsyncTeleBot instance.
    :param chat_id: The ID of the chat to send the photo to.
    :param photo: The photo to send.
    :param a: Additional positional arguments.
    :param kw: Additional keyword arguments, including the caption.
    :return: The sent photo message object.
    """
    caption: str = kw.get("caption") or ""

    # Load user settings to check if voice output is enabled.
    async with UserManager(chat_id) as s:
        voice_user = s.output_type == OutputType.VOICE

    # If voice output is enabled and a caption is present, send a voice message.
    if voice_user and caption.strip():
        await _send_voice(
            self,
            chat_id,
            caption,
            reply_to_message_id=kw.get("reply_to_message_id"),
            voice_only=True
        )

    # Send the photo after the voice message.
    return await _original_send_photo(self, chat_id, photo, *a, **kw)

# Apply the patched send_photo method to the AsyncTeleBot class.
AsyncTeleBot.send_photo = patched_send_photo  # type: ignore
