from math import sqrt, floor
from json import loads

from aiohttp import request

from telebot import types, util, formatting
from telebot.states import State, StatesGroup
from telebot.states.asyncio.context import StateContext

import aioschedule
import i18n

from .scrapper import get_data
from .models import UserSettingsManager, UserSettings
from .constants import MapProvider, UserType, UserLanguage, OutputType
from .util import haversine_distance, build_routing_data, static_map
from .message_analyser import parse_command, BotCommands, parse_time_location

from .bot import bot


#pylint: disable=too-few-public-methods
class BotUserStates(StatesGroup):
    needs_date_time = State()
    timer_set = State()
#pylint: enable=too-few-public-methods

@bot.api.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    async with bot as api:
        # Create default settings if new user
        async with UserSettingsManager(message.from_user) as s:
            if s.user_type == UserType.UNDEFINED:
                s.language = UserLanguage.DE
                s.user_type = UserType.VISITOR
        await api.send_message(
            message.chat.id,
            formatting.format_text(
                formatting.mitalic(i18n.t("strings.welcome_msg", str(s.language))),
                "",
                await bot.help_message(message.from_user)
            ),
            parse_mode="Markdown"
        )


@bot.api.message_handler(commands=["help"])
async def help_handler(message: types.Message):
    async with bot as api:
        await api.send_message(
            message.chat.id,
            await bot.help_message(message.from_user),
            parse_mode="Markdown"
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
                reply_markup=UserSettings.markup_buttons(str(s.language))
            )

            await bot.update_inline_buttons(message.from_user, sent)

            @bot.api.callback_query_handler(lambda cb : cb.message.message_id == sent.message_id)
            async def handle_settings_callback(cb : types.CallbackQuery):
                lang = str(s.language)
                match(cb.data):
                    case "user_language":
                        await api.edit_message_reply_markup(
                            sent.chat.id,
                            sent.message_id,
                            reply_markup=UserLanguage.markup_buttons(lang)
                        )
                    case "map_provider":
                        await api.edit_message_reply_markup(
                            sent.chat.id,
                            sent.message_id,
                            reply_markup=MapProvider.markup_buttons(lang)
                        )
                    case "user_type":
                        await api.edit_message_reply_markup(
                            sent.chat.id,
                            sent.message_id,
                            reply_markup=UserType.markup_buttons(lang)
                        )
                    case "output_type":
                        await api.edit_message_reply_markup(
                            sent.chat.id,
                            sent.message_id,
                            reply_markup=OutputType.markup_buttons(lang)
                        )
                    case "back":
                        await api.edit_message_reply_markup(
                            sent.chat.id,
                            sent.message_id,
                            reply_markup=UserSettings.markup_buttons(lang)
                        )
                    case _:
                        update = loads(cb.data if cb.data else "")
                        s.language = UserLanguage(update[UserLanguage.__name__]) if \
                            UserLanguage.__name__ in update else s.language
                        s.map_provider = MapProvider(update[MapProvider.__name__]) if \
                            MapProvider.__name__ in update else s.map_provider
                        s.user_type = UserType(update[UserType.__name__]) if \
                            UserType.__name__ in update else s.user_type
                        s.output_type = OutputType(update[OutputType.__name__]) \
                            if OutputType.__name__ in update else s.output_type
                        lang = str(s.language)

                        await api.edit_message_text(
                            str(s),
                            sent.chat.id,
                            sent.message_id,
                            reply_markup=UserSettings.markup_buttons(lang)
                        )

                await api.answer_callback_query(cb.id)


@bot.api.message_handler(commands=["recommend"])
async def recommend_handler(message: types.Message):
    async with UserSettingsManager(message.from_user) as s:
        lang = str(s.language)

        markup = types.ReplyKeyboardMarkup(
            row_width=1, resize_keyboard=True, one_time_keyboard=True
        )

        button_geo = types.KeyboardButton(
            text=i18n.t("strings.location_btn", lang), request_location=True
        )
        markup.add(button_geo)

        async with bot as api:
            await api.send_message(
                message.chat.id,
                i18n.t("strings.location_msg", lang),
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

        closest_park = sorted(
            [
                (
                    p,
                    haversine_distance(
                        s.last_location,
                        p.get_pos()
                    )
                )
                for p in await get_data(is_visitor)
                if not p.almost_full()
            ],
            key=lambda t: t[1]
        )[0][0]

        # Determine the map provider to use for building URLs
        button = {
            i18n.t('strings.recommended_space_nav_msg', str(s.language)):
            build_routing_data(closest_park.get_pos(), s.map_provider)
        }

        markup = util.quick_markup(button, row_width=1)

        async with bot as api:
            await bot.update_inline_buttons(
                message.from_user,
                await api.send_message(
                    message.chat.id,
                    i18n.t(
                        "strings.recommended_space_msg",
                        locale=str(s.language),
                        spot=closest_park.to_pretty(str(s.language))
                    ),
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
        parking_spots = [
            p for p in parking_spots if not p.name.name.startswith("M")
            and p.free_spaces > 0
        ]

        # At most 9, as double digits cannot be displayed on markers
        while len(parking_spots) > 9:
            parking_spots.pop()

        spot_btns = {
            f"{parking_spots.index(p) + 1}: {p.free_spaces} {p.occupancy_level()}":
                build_routing_data(p.get_pos(), s.map_provider)
            for p in parking_spots
        }

        # Fetch map and send as photo
        nav_map = static_map(markers=parking_spots)
        async with request("GET", nav_map) as req:
            async with bot as api:
                sent = await api.send_photo(
                    message.chat.id,
                    await req.read(),
                    reply_markup=util.quick_markup(
                        spot_btns,
                        row_width=floor(sqrt(len(parking_spots)))
                    )
                )

                await bot.update_inline_buttons(message.from_user, sent)

                @bot.api.callback_query_handler(lambda c : c.message.message_id == sent.message_id)
                async def handle_navigation_callback(cb : types.CallbackQuery):
                    await api.answer_callback_query(
                        cb.id,
                        formatting.format_text(
                            i18n.t("strings.mapprovider_not_set", str(s.language))
                        ),
                        True
                    )


@bot.api.message_handler(commands=["overview"])
async def overview_handler(message: types.Message):
    """
    Handler for the /overview command.
    Displays an overview of all car parks with their free spaces.
    """
    async with UserSettingsManager(message.from_user) as s:
        lang = str(s.language)
        is_visitor = s.user_type is UserType.VISITOR
        car_parks = await get_data(is_visitor)
        response = f"{i18n.t('strings.overview_campus', lang)}:\n\n"

        city_car_parks = []
        for car_park in car_parks:
            if car_park.name.name.startswith("M"):
                city_car_parks.append(car_park)
                continue

            response += car_park.to_pretty(lang)

        if len(city_car_parks) > 0:
            response += f"\n{i18n.t('strings.overview_city', lang)}:\n\n"
            for car_park in city_car_parks:
                response += car_park.to_pretty(lang)

        async with bot as api:
            await api.send_message(message.chat.id, response)


@bot.api.message_handler(commands=["timer"])
async def timing_handler(message: types.Message, state: StateContext):
    """
    Handler for the /timer command.
    Sets a timer for when the user needs a parking recommendation.
    Optionally, a location can be specified to search for a spot nearby.
    """
    async with UserSettingsManager(message.from_user) as s:
        result = await parse_time_location(message.text)
        # If no time was supplied, ask for it
        if result is None or result.time is None:
            await state.set(BotUserStates.needs_date_time)
            await bot.api.reply_to(
                message,
                i18n.t("strings.time_unknown", str(s.language))
            )
        else:
            await state.set(BotUserStates.timer_set)

            async def recommend_on_timer(msg : types.Message):
                await state.delete()
                aioschedule.clear(msg.from_user.id)
                await navigation_handler(msg)

            await bot.api.reply_to(message, i18n.t(
                "strings.timer_set" if result.location is None else "strings.timer_location_set",
                time=result.time.strftime("%H:%M"),
                date=result.time.strftime("%-d.%-m."),
                loc=result.location,
                locale=str(s.language)
            ))

            # Possibly remove existing reminder
            aioschedule.clear(message.from_user.id)
            # Determine day (-> only at most one week in the future!)
            day_of_week = result.time.strftime("%A").lower()
            # pylint: disable=no-member
            aioschedule.every().on(day_of_week).at(
                result.time.strftime("%H:%M")
            ).do(recommend_on_timer, msg=message).tag(message.from_user.id)
            # pylint: enable=no-member


@bot.api.message_handler(content_types="text")
async def free_text_handler(message: types.Message, state: StateContext):
    """
    Handles free inputs from the user, such as text messages (or audio?).
    Attempts to map the input to one of the available commands and executes it.
    If not command could be detected, a clarification message is sent instead.
    """
    # Skip free text if we are waiting for a time input
    if await state.get() == BotUserStates.needs_date_time:
        await timing_handler(message, state)
        return

    parsed = await parse_command(message.text)
    match parsed:
        case BotCommands.NAVIGATION:
            await navigation_handler(message)
        case BotCommands.TIMER:
            await timing_handler(message, state)
        case BotCommands.RECOMMEND:
            await recommend_handler(message)
        case BotCommands.OVERVIEW:
            await overview_handler(message)
        case _:
            async with UserSettingsManager(message.from_user) as s:
                await bot.api.reply_to(
                    message,
                    formatting.format_text(
                        i18n.t("strings.command_unknown", str(s.language)),
                        await bot.help_message(message.from_user)
                    ),
                    parse_mode="Markdown"
                )
