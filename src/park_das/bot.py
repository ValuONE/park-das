import os

import telebot
from telebot import types

from .models import UserSettingsManager, InlineButtons

class ParkBot:
    def __init__(self) -> None:
        try:
            token = os.environ["TOKEN"]
        except KeyError as e:
            raise ValueError("TOKEN environment variable is not set or is empty.") from e

        self._bot = telebot.TeleBot(token)

        self._bot.set_my_commands(
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
                    "navigation",
                    "Listet alle verfügbaren Parkplätze als navigierbare Buttons auf."
                )
            ]
        )

    def __del__(self):
        self._bot.stop_polling()
        del self._bot

    def __enter__(self) -> telebot.TeleBot:
        return self._bot

    def __exit__(self, exception_type, exception_val, trace):
        return True

    @property
    def api(self) -> telebot.TeleBot:
        """
        Access to the bot API
        """
        return self._bot

    def update_inline_buttons(self, user : types.User, message : types.Message):
        """
        Ensures only one set of inline buttons is present.
        
        Args:
            user (User) : User the inline buttons are sent to
            message (Message) : New message containing inline buttons
        """
        with UserSettingsManager(user.id) as mgr:
            if mgr.settings.inline_button is not None:
                self._bot.delete_message(mgr.settings.inline_button.chat_id,
                                         mgr.settings.inline_button.message_id)
                mgr.settings.inline_button = InlineButtons(message.chat.id, message.message_id)


# Global instance to be used when doing anything with the API
bot = ParkBot()
