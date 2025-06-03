from math import sqrt, floor
from json import loads

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
        with UserSettingsManager(message.from_user) as settings:
            if settings.user_type == UserType.UNDEFINED:
                settings.language = UserLanguage.DE
                settings.map_provider = MapProvider.GOOGLE
                settings.user_type = UserType.STUDENT
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
        with UserSettingsManager(message.from_user) as settings:
            sent = api.send_message(
                message.chat.id,
                str(settings),
                reply_markup=UserSettings.markup_buttons()
            )

        bot.update_inline_buttons(message.from_user, sent)

        @bot.api.callback_query_handler(lambda cb : cb.message.message_id == sent.message_id)
        def handle_settings_callback(cb : types.CallbackQuery):
            match(cb.data):
                case "user_language":
                    api.edit_message_reply_markup(
                        sent.chat.id,
                        sent.message_id,
                        reply_markup=UserLanguage.markup_buttons()
                    )
                case "map_provider":
                    api.edit_message_reply_markup(
                        sent.chat.id,
                        sent.message_id,
                        reply_markup=MapProvider.markup_buttons()
                    )
                case "user_type":
                    api.edit_message_reply_markup(
                        sent.chat.id,
                        sent.message_id,
                        reply_markup=UserType.markup_buttons()
                    )
                case "back":
                    api.edit_message_reply_markup(
                        sent.chat.id,
                        sent.message_id,
                        reply_markup=UserSettings.markup_buttons()
                    )
                case _:
                    update = loads(cb.data if cb.data else "")
                    with UserSettingsManager(cb.from_user) as settings:
                        settings.language = UserLanguage(update[UserLanguage.__name__]) if \
                            UserLanguage.__name__ in update else settings.language
                        settings.map_provider = MapProvider(update[MapProvider.__name__]) if \
                            MapProvider.__name__ in update else settings.map_provider
                        settings.user_type = UserType(update[UserType.__name__]) if \
                            UserType.__name__ in update else settings.user_type

                        api.edit_message_text(
                            str(settings),
                            sent.chat.id,
                            sent.message_id
                        )

                    api.edit_message_reply_markup(
                        sent.chat.id,
                        sent.message_id,
                        reply_markup=UserSettings.markup_buttons()
                    )

            api.answer_callback_query(cb.id)


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
    """Handles the user‑shared location from the *live* flow.

    Computes the distance to every car park, sorts the list *ascending* by
    distance and finally replies with an **inline‑keyboard** (one button per
    park) – exactly like */navigation*, just ordered by proximity.
    """
    if not message.location:
        return

    lat = message.location.latitude
    lon = message.location.longitude

    # Gets the parking data
    carparks = fetch_data(is_visitor=False)

    # Calculates distances to each parking slot
    carparks_with_distance = []
    for carpark in carparks:
        park = carpark.get_pos()
        distance = simple_distance(lat, lon, park.latitude, park.longitude)
        carparks_with_distance.append((carpark, distance))

    # Sorts the car slots by distance (ascending)
    carparks_with_distance.sort(key=lambda x: x[1])

    with bot as api:

        def emojify(free: int, total: int) -> str:
            ratio = free / total
            if ratio > 0.25:
                return "✅"
            if 0.05 < ratio < 0.25:
                return "⚠️"
            return "❌"

        spots = {
            f"{emojify(carpark.free_spaces, carpark.total_spaces)} "  # Availability symbol
            f"{carpark.name.value}: {carpark.free_spaces} | "         # Text
            f"{distance:.1f} km": {
                "url": build_googlemaps_url(carpark.get_pos())
            }
            for carpark, distance in carparks_with_distance
        }

        spots_buttons = util.quick_markup(
            spots,
            row_width=1
        )

        match(MapProviders.GOOGLE):
            case MapProviders.GOOGLE:
                bot.update_inline_buttons(
                    message.from_user,
                    api.send_message(
                        message.chat.id,
                        "Nächste Parkplätze:",
                        reply_markup=spots_buttons,
                    ),
                )
            case MapProviders.APPLE:
                api.send_message(
                    message.chat.id,
                    "Noch nicht implementiert!"
                )

@bot.api.message_handler(commands=["navigation"])
def nav_helper(message: types.Message):
    with UserSettingsManager(message.from_user) as settings:
        cached = settings

    parking_spots = fetch_data(cached.user_type == UserType.VISITOR)
    parking_spots.sort(key=lambda val : val.free_spaces, reverse=True)

    with bot as api:

        def emojify(free, total):
            ratio = free / total
            if ratio > 0.25:
                return "✅"
            if 0.05 < ratio < 0.25:
                return "⚠️"
            return "❌"

        match(cached.map_provider):
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
