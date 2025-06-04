from math import sqrt, floor
from json import loads

from telebot import types, util, formatting

from .navigation_builders import build_routing_data
from .scrapper import get_data
from .models import UserSettingsManager, UserSettings
from .constants import MapProvider, UserType, UserLanguage
from .distance import simple_distance

from .bot import bot

@bot.api.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    async with bot as api:
        # Create default settings if new user
        async with UserSettingsManager(message.from_user) as s:
            if s.user_type == UserType.UNDEFINED:
                s.language = UserLanguage.DE
                s.map_provider = MapProvider.GOOGLE
                s.user_type = UserType.STUDENT
        await api.send_message(
            message.chat.id,
            formatting.format_text(
                formatting.mitalic("🤖 Willkommen bei ParkBot 🚘"),
                "",
                await help_message()
            ),
            parse_mode="Markdown"
        )


@bot.api.message_handler(commands=["help"])
async def help_handler(message: types.Message):
    async with bot as api:
        await api.send_message(
            message.chat.id,
            await help_message(),
            parse_mode="Markdown"
        )


async def help_message() -> str:
    cmds = await bot.api.get_my_commands(scope=None, language_code=None)
    cmds_str = "\n".join([f"/{cmd.command} : {cmd.description}" for cmd in cmds])
    return formatting.format_text(
        formatting.mbold("Folgende Befehle sind verfügbar:"),
        cmds_str
    )


@bot.api.message_handler(commands=["settings"])
async def settings_handler(message: types.Message):
    """
    Handler for the /settings command
    Displays current settings in text message and inline buttons to adjust settings.
    """
    async with UserSettingsManager(message.from_user) as s:
        async with bot as api:
            sent = await api.send_message(
                message.chat.id,
                str(s),
                reply_markup=UserSettings.markup_buttons()
            )

            await bot.update_inline_buttons(message.from_user, sent)

            @bot.api.callback_query_handler(lambda cb : cb.message.message_id == sent.message_id)
            async def handle_settings_callback(cb : types.CallbackQuery):
                match(cb.data):
                    case "user_language":
                        await api.edit_message_reply_markup(
                            sent.chat.id,
                            sent.message_id,
                            reply_markup=UserLanguage.markup_buttons()
                        )
                    case "map_provider":
                        await api.edit_message_reply_markup(
                            sent.chat.id,
                            sent.message_id,
                            reply_markup=MapProvider.markup_buttons()
                        )
                    case "user_type":
                        await api.edit_message_reply_markup(
                            sent.chat.id,
                            sent.message_id,
                            reply_markup=UserType.markup_buttons()
                        )
                    case "back":
                        await api.edit_message_reply_markup(
                            sent.chat.id,
                            sent.message_id,
                            reply_markup=UserSettings.markup_buttons()
                        )
                    case _:
                        update = loads(cb.data if cb.data else "")
                        s.language = UserLanguage(update[UserLanguage.__name__]) if \
                            UserLanguage.__name__ in update else s.language
                        s.map_provider = MapProvider(update[MapProvider.__name__]) if \
                            MapProvider.__name__ in update else s.map_provider
                        s.user_type = UserType(update[UserType.__name__]) if \
                            UserType.__name__ in update else s.user_type

                        await api.edit_message_text(
                            str(s),
                            sent.chat.id,
                            sent.message_id,
                            reply_markup=UserSettings.markup_buttons()
                        )

                await api.answer_callback_query(cb.id)


@bot.api.message_handler(commands=["live"])
async def live_handler(message: types.Message):
    markup = types.ReplyKeyboardMarkup(
        row_width=1, resize_keyboard=True, one_time_keyboard=True
    )
    button_geo = types.KeyboardButton(
        text="📍 Standort senden", request_location=True
    )
    markup.add(button_geo)

    async with bot as api:
        await api.send_message(
            message.chat.id,
            "Tippe auf „📍 Standort senden“, um mir deine aktuelle Position zu schicken.",
            reply_markup=markup,
        )


@bot.api.message_handler(content_types=["location"])
async def location_handler(message: types.Message):
    """
    Receives user's location and returns sorted car parks.
    """
    if not message.location:
        return

    async with UserSettingsManager(message.from_user) as s:
        s.last_location = message.location
        is_visitor = s.user_type == UserType.VISITOR

        carparks = await get_data(is_visitor)

        carparks_with_distance = [
            (
                p,
                simple_distance(
                    s.last_location.latitude,
                    s.last_location.longitude,
                    p.get_pos().latitude,
                    p.get_pos().longitude
                )
            )
            for p in carparks
        ]
        carparks_with_distance.sort(key=lambda t: t[1])

        # Determine the map provider to use for building URLs
        buttons = {
            f"{p.emojify_status()} "
            f"{p.name.value}: {p.free_spaces} | {dist:.1f} km":
                build_routing_data(p.get_pos(), s.map_provider)
            for p, dist in carparks_with_distance
        }

        markup = util.quick_markup(buttons, row_width=1)

        async with bot as api:
            await bot.update_inline_buttons(
                message.from_user,
                await api.send_message(
                    message.chat.id,
                    "Nächste Parkplätze:",
                    reply_markup=markup
                )
            )


@bot.api.message_handler(commands=["navigation"])
async def navigation_handler(message: types.Message):
    """
    Handler for the /navigation command.
    Displays inline buttons that can navigate to corresponding parking lots.
    """
    async with UserSettingsManager(message.from_user) as s:
        parking_spots = await get_data(s.user_type == UserType.VISITOR)
        parking_spots.sort(key=lambda p: p.free_spaces, reverse=True)

        spots = {
            f"{p.emojify_status()} {p.name.name}: {p.free_spaces}":
                build_routing_data(p.get_pos(), s.map_provider)
            for p in parking_spots
        }

        buttons = util.quick_markup(spots, row_width=floor(sqrt(len(parking_spots))))

        async with bot as api:
            sent = await api.send_message(
                message.chat.id,
                "Verfügbare Parkplätze:",
                reply_markup=buttons
            )

            await bot.update_inline_buttons(message.from_user, sent)

            @bot.api.callback_query_handler(lambda cb : cb.message.message_id == sent.message_id)
            async def handle_navigation_callback(cb : types.CallbackQuery):
                await api.answer_callback_query(
                    cb.id,
                    "⚠️ Es ist kein Kartenanbieter gesetzt ⚠️",
                    True
                )


@bot.api.message_handler(commands=["overview"])
async def overview_handler(message: types.Message):
    """
    Handler for the /overview command.
    Displays an overview of all car parks with their free spaces.
    """
    async with UserSettingsManager(message.from_user) as s:
        is_visitor = s.user_type is UserType.VISITOR
        car_parks = await get_data(is_visitor)
        response = "🎓 Universitätsparkplätze:\n\n"

        city_car_parks = []
        for car_park in car_parks:
            if car_park.name.name.startswith("M"):
                city_car_parks.append(car_park)
                continue

            response += car_park.to_pretty()

        if len(city_car_parks) > 0:
            response += "\n🏙️ Stadtparkplätze:\n\n"
            for car_park in city_car_parks:
                response += car_park.to_pretty()

        async with bot as api:
            await api.send_message(message.chat.id, response)
