import telebot
from telebot import types

from .bot import bot

@bot.api.message_handler(commands=["start"])
def start_handler(message : types.Message):
    with bot as api:
        api.send_message(message.chat.id, "Willkommen bei ParkBot!")
        api.send_message(message.chat.id, help_message())

@bot.api.message_handler(commands=["help"])
def help_handler(message : types.Message):
    with bot as api:
        api.send_message(message.chat.id, help_message())

def help_message() -> str:
    help_txt = "Folgende Befehle sind verfügbar:\n"
    return help_txt + "".join([f"/{cmd.command} : {cmd.description}\n" for cmd in bot.api.get_my_commands()])
