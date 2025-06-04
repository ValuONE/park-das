from math import sqrt, floor
from json import loads

from telebot import types, util, formatting

from .navigation_builders import build_googlemaps_url, build_applemaps_url
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
    """
    Handler for the /settings command
    Displays current settings in text message and inline buttons to adjust settings.
    """
    with UserSettingsManager(message.from_user) as settings:
        with bot as api:
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
    if not message.location:
        return

    lat, lon = message.location.latitude, message.location.longitude

    with UserSettingsManager(message.from_user) as settings:
        is_visitor = settings.user_type == UserType.VISITOR

    carparks = fetch_data(is_visitor=is_visitor)

    carparks_with_distance = [
        (
            p,
            simple_distance(
                lat,
                lon,
                p.get_pos().latitude,
                p.get_pos().longitude
            )
        )
        for p in carparks
    ]
    carparks_with_distance.sort(key=lambda t: t[1])

    # Determine the map provider to use for building URLs
    with UserSettingsManager(message.from_user) as s:
        build_url = (
            build_googlemaps_url
            if s.map_provider == MapProvider.GOOGLE
            else build_applemaps_url
        )

    def emojify(free, total):
        ratio = free / total
        return "✅" if ratio > .25 else "⚠️" if ratio > .05 else "❌"

    buttons = {
        f"{emojify(p.free_spaces, p.total_spaces)} "
        f"{p.name.value}: {p.free_spaces} | {dist:.1f} km":
            {"url": build_url(p.get_pos())}
        for p, dist in carparks_with_distance
    }

    markup = util.quick_markup(buttons, row_width=1)

    with bot as api:
        bot.update_inline_buttons(
            message.from_user,
            api.send_message(message.chat.id, "Nächste Parkplätze:", reply_markup=markup)
        )


@bot.api.message_handler(commands=["navigation"])
def nav_helper(message: types.Message):
    with UserSettingsManager(message.from_user) as s:
        user_settings = s

    parking_spots = fetch_data(user_settings.user_type == UserType.VISITOR)
    parking_spots.sort(key=lambda p: p.free_spaces, reverse=True)

    build_url = (
        build_googlemaps_url
        if user_settings.map_provider == MapProvider.GOOGLE
        else build_applemaps_url
    )

    def emojify(free, total):
        ratio = free / total
        return "✅" if ratio > .25 else "⚠️" if ratio > .05 else "❌"

    spots = {
        f"{emojify(p.free_spaces, p.total_spaces)} {p.name.name}: {p.free_spaces}": {
            "url": build_url(p.get_pos())
        }
        for p in parking_spots
    }

    markup = util.quick_markup(spots, row_width=floor(sqrt(len(parking_spots))))

    with bot as api:
        bot.update_inline_buttons(
            message.from_user,
            api.send_message(message.chat.id, "Verfügbare Parkplätze:", reply_markup=markup)
        )
