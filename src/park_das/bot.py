import os
import telebot
from telebot import types

class ParkBot(object):
    _instance = None

    def __new__(cls):
        """
        Singleton für Zugriff auf Bot API
        """
        if cls._instance is None:
            cls._instance = super(ParkBot, cls).__new__(cls)

            try:
                token = os.environ["TOKEN"]
            except KeyError:
                raise ValueError("TOKEN environment variable is not set or is empty.")

            cls._bot = telebot.TeleBot(token)

        return cls._instance

    @property
    def bot(cls) -> telebot.TeleBot:
        """
        Getter für Bot API
        """
        return cls._bot

    @classmethod
    def setup(cls):
        """
        Bot Setup, bspw. setzen der Kommandos
        """
        cls().bot.set_my_commands(
            [
                types.BotCommand("start", "Initalisiert den Bot und listet verfügbare Kommandos auf."),
                types.BotCommand("help", "Listet verfügbare Kommandos auf."),
            ]
        )