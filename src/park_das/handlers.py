from math import sqrt, floor

from telebot import types, util, formatting

from .navigation_builders import build_googlemaps_url
from .scrapper import fetch_data
from .models import UserSettingsManager, UserSettings
from .constants import MapProvider, UserType, UserLanguage
from .distance import simple_distance

from .bot import bot


@bot.api.message_handler(commands=["start"])
def start_handler(message: types.Message):
    with bot as api:
        # Create default settings if new user
        with UserSettingsManager(message.from_user) as mgr:
            if mgr.settings.user_type == UserType.UNDEFINED:
                mgr.settings = UserSettings(UserLanguage.DE, MapProvider.GOOGLE, UserType.STUDENT)
        api.send_message(message.chat.id, "Willkommen bei ParkBot!")
        api.send_message(message.chat.id, help_message())


@bot.api.message_handler(commands=["help"])
def help_handler(message: types.Message):
    with bot as api:
        api.send_message(message.chat.id, help_message())


def help_message() -> str:
    help_msg = "Folgende Befehle sind verfügbar:"
    commands = "\n".join(
        [f"/{cmd.command} : {cmd.description}" for cmd in bot.api.get_my_commands()]
    )
    return formatting.format_text(help_msg, commands)


@bot.api.message_handler(commands=["settings"])
def settings_handler(message: types.Message):
    with bot as api:
        with UserSettingsManager(message.from_user) as mgr:
            api.reply_to(
                message,
                str(mgr.settings)
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
    Receives user's location and returns sorted car parks.
    """
    if not message.location:
        return

    lat = message.location.latitude
    lon = message.location.longitude

    # Gets the parking data
    carparks = fetch_data(is_visitor=True)

    # Calculates distances to each parking slot
    carparks_with_distance = []
    for carpark in carparks:
        park = carpark.get_pos()
        distance = simple_distance(lat, lon, park.latitude, park.longitude)
        carparks_with_distance.append((carpark, distance))

    # Sorts the car slots by distance
    carparks_with_distance.sort(key=lambda x: x[1])

    # creates the response message
    response = "🚗 Nächste Parkplätze:\n\n"
    for carpark, distance in carparks_with_distance:
        response += \
            (
                f"{carpark.name.value}: "
                f"{carpark.free_spaces} frei — "
                f"{distance:.1f} km entfernt\n"
            )

    remove_keyboard = types.ReplyKeyboardRemove()

    # Sends the response message
    with bot as api:
        api.send_message(
            message.chat.id,
            response,
            reply_markup=remove_keyboard
        )


@bot.api.message_handler(commands=["navigation"])
def nav_helper(message: types.Message):
    with UserSettingsManager(message.from_user) as mgr:
        parking_spots = fetch_data(mgr.settings.user_type == UserType.VISITOR)
        parking_spots.sort(key=lambda val : val.free_spaces, reverse=True)

        with bot as api:

            def emojify(free, total):
                ratio = free / total
                if ratio > 0.25:
                    return "✅"
                if 0.05 < ratio < 0.25:
                    return "⚠️"
                return "❌"

            match(MapProvider.GOOGLE):
                case MapProvider.GOOGLE:
                    spots = {
                        (
                            f"{emojify(spot.free_spaces, spot.total_spaces)} "
                            f"{spot.name.name}: {spot.free_spaces}"
                        ): {
                            "url" : build_googlemaps_url(spot.get_pos())
                        } for spot in parking_spots}

                    spots_buttons = util.quick_markup(
                        spots,
                        row_width=floor(sqrt(len(parking_spots)))
                    )

                    buttons_msg = api.send_message(
                        message.chat.id,
                        "Verfügbare Parkplätze:",
                        reply_markup=spots_buttons
                    )

                    bot.update_inline_buttons(
                        message.from_user,
                        buttons_msg
                    )
                case MapProvider.APPLE:
                    api.send_message(
                        message.chat.id,
                        "Noch nicht implementiert!"
                    )
