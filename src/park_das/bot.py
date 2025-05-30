import os

import telebot
from telebot import types

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
        Getter für Bot API
        """
        return self._bot


# Global instance to be used when doing anything with the API
bot = ParkBot()
