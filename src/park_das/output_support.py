from __future__ import annotations
import asyncio, os, tempfile
import aiosqlite
from gtts import gTTS                      # pip install gTTS
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from .constants import OutputType


# ---------- kleine Hilfsfunktionen -----------------------------------------
def _iso_lang(db_value: str | None) -> str:
    # "settings.language.de" -> "de"
    return (db_value or "en").rsplit(".", 1)[-1]

async def _pref(chat_id: int) -> tuple[bool, str]:
    """suche Sprache & Output-Modus des Users im DB-Table settings"""
    async with aiosqlite.connect("settings.db") as con:
        async with con.execute(
            "SELECT output_type, language FROM settings WHERE user_id = ?",
            (chat_id,),
        ) as cur:
            row = await cur.fetchone()
            if row is None:
                return False, "en"
            return row[0] == repr(OutputType.VOICE), _iso_lang(row[1])

async def _tts(text: str, lang: str) -> str:
    """Text->Speech → speichere temporäre MP3 und liefere Pfad zurück"""
    fd, path = tempfile.mkstemp(suffix=".mp3"); os.close(fd)
    await asyncio.get_running_loop().run_in_executor(
        None, lambda: gTTS(text, lang=lang).save(path)
    )
    return path


# ---------- Monkey-Patches ---------------------------------------------------
_original_send_message = AsyncTeleBot.send_message
_original_reply_to    = AsyncTeleBot.reply_to

async def _send_voice(self: AsyncTeleBot, chat_id: int, text: str, **kw):
    use_voice, lang = await _pref(chat_id)
    if not use_voice:                               # ➜ normaler Text
        return await _original_send_message(self, chat_id, text, **kw)

    path = await _tts(text, lang)
    try:
        # Parse-Mode ignorieren – Markdown in Voice-Captions ist unzuverlässig
        kw.pop("parse_mode", None)
        res = await self.send_voice(chat_id, open(path, "rb"), caption=text, **kw)
    finally:
        try: os.remove(path)
        except OSError: pass
    return res

async def patched_send_message(self, chat_id, text, *a, **kw):  # type: ignore
    return await _send_voice(self, chat_id, text, *a, **kw)

async def patched_reply_to(self, msg: types.Message, text, *a, **kw):  # type: ignore
    return await _send_voice(self, msg.chat.id, text,
                             reply_to_message_id=msg.message_id, *a, **kw)

AsyncTeleBot.send_message = patched_send_message  # type: ignore
AsyncTeleBot.reply_to     = patched_reply_to      # type: ignore