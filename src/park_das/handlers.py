from telebot import types

from .bot import bot


@bot.api.message_handler(commands=["start"])
def start_handler(message: types.Message):
    with bot as api:
        api.send_message(message.chat.id, "Willkommen bei ParkBot!")
        api.send_message(message.chat.id, help_message())


@bot.api.message_handler(commands=["help"])
def help_handler(message: types.Message):
    with bot as api:
        api.send_message(message.chat.id, help_message())


def help_message() -> str:
    help_txt = "Folgende Befehle sind verfügbar:\n"
    return help_txt + "".join(
        [f"/{cmd.command} : {cmd.description}\n" for cmd in bot.api.get_my_commands()]
    )

@bot.api.message_handler(commands=["live"])
def live_handler(message: types.Message):
    markup = types.ReplyKeyboardMarkup(
        row_width=1, resize_keyboard=True, one_time_keyboard=True
    )
    button_geo = types.KeyboardButton(
        text="📍 Standort senden", request_location=True
    )
    markup.add(button_geo)

    with bot as api:
        api.send_message(
            message.chat.id,
            "Tippe auf „📍 Standort senden“, um mir deine aktuelle Position zu schicken.",
            reply_markup=markup,
        )

@bot.api.message_handler(content_types=["location"])
def location_handler(message: types.Message):
    """
    Returns the user's current location he sent to the bot.
    """
    if not message.location:       # Safety-Check
        return

    lat = message.location.latitude
    lon = message.location.longitude

    remove_keyboard = types.ReplyKeyboardRemove()

    with bot as api:
        api.send_message(
            message.chat.id,
            f"Dein aktueller Standort:\n• Breitengrad: {lat}\n• Längengrad: {lon}",
            reply_markup=remove_keyboard,
        )
