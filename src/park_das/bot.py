import os

from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot import types

from .models import UserSettingsManager, InlineButtons

class ParkBot:

    def __init__(self) -> None:
        try:
            token = os.environ["TOKEN"]
        except KeyError as e:
            raise ValueError("TOKEN environment variable is not set or is empty.") from e

        data = StateMemoryStorage()
        self._bot = AsyncTeleBot(token, state_storage=data)

    async def setup_bot(self):
        """
        Creates bot commands, does all initialization
        """
        await self.api.delete_my_commands()
        await self.api.set_my_commands(
            [
                types.BotCommand(
                    "start",
                    "Initalisiert den Bot und listet verfügbare Kommandos auf."
                ),
                types.BotCommand(
                    "help",
                    "Listet verfügbare Kommandos auf."
                ),
                types.BotCommand(
                    "settings",
                    "Listet die aktuellen Einstellungen."
                ),
                types.BotCommand(
                    "overview",
                    "Listet alle verfügbaren Parkplätze auf."
                ),
                types.BotCommand(
                    "live",
                    "Ermöglicht senden des aktuellen Standorts."
                ),
                types.BotCommand(
                    "navigation",
                    "Listet alle verfügbaren Parkplätze als navigierbare Buttons auf."
                )
            ]
        )

    async def __aenter__(self) -> AsyncTeleBot:
        return self._bot

    async def __aexit__(self, exception_type, exception_val, trace):
        return True

    @property
    def api(self) -> AsyncTeleBot:
        """
        Access to the bot API
        """
        return self._bot

    async def update_inline_buttons(self, user : types.User | None, message : types.Message):
        """
        Ensures only one set of inline buttons is present.
        
        Args:
            user (User) : User the inline buttons are sent to
            message (Message) : New message containing inline buttons
        """
        async with UserSettingsManager(user) as s:
            if s.inline_buttons is not None:
                await self.api.delete_message(s.inline_buttons.chat_id,
                                              s.inline_buttons.message_id)
            s.inline_buttons = InlineButtons(message.chat.id, message.message_id)


# Global instance to be used when doing anything with the API
bot = ParkBot()
