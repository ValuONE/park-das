from math import sqrt, floor

from telebot import types, util

from .navigation_builders import build_googlemaps_url
from .scrapper import fetch_data
from .constants import MapProviders
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

@bot.api.message_handler(commands=["navigation"])
def nav_helper(message: types.Message):
    parking_spots = fetch_data(False)
    parking_spots.sort(key=lambda val : val.free_spaces, reverse=True)

    with bot as api:

        def emojify(free, total):
            ratio = free / total
            if ratio > 0.25:
                return "✅"
            if 0.05 < ratio < 0.25:
                return "⚠️"
            return "❌"

        spots = {f"{emojify(spot.free_spaces, spot.total_spaces)} " +
                 f"{spot.name.name}: {spot.free_spaces}": {
            "url" : build_googlemaps_url(spot.get_pos())
            } for spot in parking_spots}
        spots_buttons = util.quick_markup(spots, row_width=floor(sqrt(len(parking_spots))))

        match(MapProviders.GOOGLE):
            case MapProviders.GOOGLE:
                bot.update_inline_buttons(message.from_user, api.send_message(message.chat.id,
                    "Verfügbare Parkplätze:", reply_markup=spots_buttons))
            case MapProviders.APPLE:
                api.send_message(message.chat.id, "Noch nicht implementiert!")
