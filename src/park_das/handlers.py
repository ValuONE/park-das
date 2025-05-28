import telebot
from telebot import types

from .bot import ParkBot

@ParkBot().bot.message_handler(commands=["start"])
def start_handler(message : types.Message):
    ParkBot().bot.send_message(message.chat.id, "Willkommen bei ParkBot!")
    ParkBot().bot.send_message(message.chat.id, help_message())

@ParkBot().bot.message_handler(commands=["help"])
def help_handler(message : types.Message):
    ParkBot().bot.send_message(message.chat.id, help_message())

def help_message() -> str:
    help_txt = "Folgende Befehle sind verfügbar:\n"
    return help_txt + "".join([f"/{cmd.command} : {cmd.description}\n" for cmd in ParkBot().bot.get_my_commands()])
