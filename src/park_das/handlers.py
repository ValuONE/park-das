from math import sqrt, floor
from json import loads

from aiofiles import open as aiopen
from aiohttp import request

from telebot import types, util, formatting

import i18n

from .scrapper import get_data
from .models import UserManager, UserData, Room
from .constants import  MapProvider, UserType, UserLanguage, OutputType, \
                        InteractionStates, RoomNames, Callbacks, Settings, BotCommands
from .util import haversine_distance, build_routing_data, static_map, check_json
from .message_analyser import parse_command, parse_time_location
from .voice_support import transcripe

from .bot import bot

@bot.api.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    """
    Handler for the /start command.
    Creates user settings for new users, sends help message.
    """
    async with bot as api:
        async with UserManager(message.from_user) as s:
            # Create default settings if new user
            if s.user_type == UserType.UNDEFINED:
                s.language = UserLanguage.DE
                s.user_type = UserType.VISITOR
                s.output_type = OutputType.TEXT

            # Reset everything
            s.bot_state = InteractionStates.IDLE
            await bot.update_bot_location(
                message.from_user,
                None,
                message.chat.id
            )

            await api.send_message(
                message.chat.id,
                formatting.format_text(
                    formatting.mitalic(i18n.t("welcome.msg", str(s.language))),
                    "",
                    await bot.help_message(str(s.language))
                ),
                parse_mode="Markdown"
            )


@bot.api.message_handler(commands=["help"])
async def help_handler(message: types.Message):
    """
    Handler for the /help command.
    Sends a message containing available commands.
    """
    async with bot as api:
        async with UserManager(message.from_user) as s:
            s.bot_state = InteractionStates.IDLE
            await api.send_message(
                message.chat.id,
                await bot.help_message(str(s.language)),
                parse_mode="Markdown"
            )


@bot.api.callback_query_handler(
    func=lambda cb: cb.data is not None and check_json(cb.data)
)
async def handle_settings_callback(cb: types.CallbackQuery):
    """
    Handles callback queries that contain callback data.

    This function processes user interactions, and more:
    - Navigate between different settings categories (e.g., language, map provider).
    - Update specific settings by selecting options.
    - Informing the user if no map provider has been selected.
    - Handle fallback cases for unknown callbacks.

    :param cb: Object containing original message and callback data.
    """
    async with bot as api:
        async with UserManager(cb.from_user.id) as s:
            lang = str(s.language)
            data : dict = loads(cb.data) # type: ignore

            # Only respond if the callback is related to the settings message
            if not s.inline_buttons.exists or cb.message.message_id != s.inline_buttons.message_id:
                return await api.answer_callback_query(cb.id)

            match data.get("type"):
                case Callbacks.MAP_PROVIDER_ERROR:
                    await api.answer_callback_query(
                        cb.id,
                        formatting.format_text(
                            i18n.t("error.mapprovider_not_set", lang)
                        ),
                        True
                    )
                case Callbacks.SETTINGS_BACK:
                    await api.edit_message_reply_markup(
                        cb.message.chat.id,
                        cb.message.message_id,
                        reply_markup=UserData.markup_buttons(lang)
                    )
                    return await api.answer_callback_query(cb.id)
                case Callbacks.SETTINGS_SELECT:
                    selected = Settings.parse(data.get("select"))
                    await api.edit_message_reply_markup(
                        cb.message.chat.id,
                        cb.message.message_id,
                        reply_markup=selected.value.markup_buttons(lang)
                    )
                    await api.answer_callback_query(cb.id)
                case Callbacks.SETTINGS_UPDATE:
                    old_output = s.output_type
                    # Update user settings based on the parsed JSON data
                    if UserLanguage.__name__ in data:
                        s.language = UserLanguage(data[UserLanguage.__name__])
                        lang = str(s.language)
                    if MapProvider.__name__ in data:
                        s.map_provider = MapProvider(data[MapProvider.__name__])
                    if UserType.__name__ in data:
                        s.user_type = UserType(data[UserType.__name__])
                    if OutputType.__name__ in data:
                        s.output_type = OutputType(data[OutputType.__name__])

                    # Handle special case for OutputType change
                    if old_output != s.output_type:
                        # Send a new message based on the updated OutputType
                        sent = await api.send_message(
                            cb.message.chat.id,
                            str(s),
                            reply_markup=UserData.markup_buttons(lang),
                            voice_only=s.output_type==OutputType.VOICE # type: ignore
                        )

                        # Update the inline buttons reference
                        await bot.update_inline_buttons(cb.from_user, sent)
                        await api.answer_callback_query(cb.id)
                    else:
                        # If no OutputType change, simply edit the text and buttons
                        await api.edit_message_text(
                            str(s),
                            cb.message.chat.id,
                            cb.message.message_id,
                            reply_markup=UserData.markup_buttons(lang),
                            parse_mode="Markdown"
                        )
                        await api.answer_callback_query(cb.id)
                case _:
                    await api.answer_callback_query(
                        cb.id,
                        i18n.t("error.callback", lang),
                        show_alert=True
                    )


@bot.api.message_handler(commands=["settings"])
async def settings_handler(message: types.Message):
    """
    Handler for the /settings command
    Displays current settings in text message and inline buttons to adjust settings.
    """
    async with UserManager(message.from_user) as s:
        s.bot_state = InteractionStates.IDLE
        async with bot as api:
            sent = await api.send_message(
                message.chat.id,
                str(s),
                reply_markup=UserData.markup_buttons(str(s.language))
            )

            await bot.update_inline_buttons(message.from_user, sent)


@bot.api.message_handler(commands=["automatic"])
async def automatic_handler(message: types.Message):
    """
    Handler for the /automatic command.
    Sends a tutorial for how to activate the functionality.
    """
    async with UserManager(message.from_user) as s:
        s.bot_state = InteractionStates.IDLE
        async with aiopen("assets/automatic_tutorial.png", "rb") as f:
            await bot.api.send_photo(
                message.chat.id,
                await f.read(),
                caption=i18n.t(
                    "automatic.tutorial",
                    str(s.language)
                )
            )


@bot.api.message_handler(commands=["recommend"])
async def recommend_handler(message: types.Message):
    """
    Handler for the /recommend command.
    Requests the location from the user in a reply keyboard.
    """
    async with UserManager(message.from_user) as s:
        s.bot_state = InteractionStates.IDLE

        # Check if user wants a recommendation for a specific location
        parsed_loc =    (await parse_time_location(message.text, s.timer)).location\
                        if s.timer.location == RoomNames.UNDEFINED\
                        else s.timer.location
        if parsed_loc != RoomNames.UNDEFINED:
            # Get the location, pass to location handler
            message.location = Room(parsed_loc).geo_pos
            await location_handler(message)
        else:
            # If no location information was available, ask for user's location
            markup = types.ReplyKeyboardMarkup(
                row_width=1, resize_keyboard=True, one_time_keyboard=True
            )

            button_geo = types.KeyboardButton(
                text=i18n.t("location.btn", str(s.language)), request_location=True
            )
            markup.add(button_geo)

            async with bot as api:
                await api.send_message(
                    message.chat.id,
                    i18n.t("location.msg", str(s.language)),
                    reply_markup=markup,
                )


@bot.api.message_handler(content_types=["proximity_alert_triggered"])
async def service_handler(message: types.Message):
    """
    Handler for the automatic parking recommendation.
    Triggers when user's live location is close enough to campus / inner city.
    """
    async with UserManager(message.from_user) as s:
        if not s.bot_state == InteractionStates.PROXIMITY_TRIGGERED:
            s.bot_state = InteractionStates.PROXIMITY_TRIGGERED
            await bot.api.send_message(
                message.chat.id,
                i18n.t("automatic.triggered", str(s.language))
            )


@bot.api.message_handler(content_types=["location"])
@bot.api.edited_message_handler(content_types=["location"])
async def location_handler(message: types.Message):
    """
    If a user's current location is recieved, sends a recommended parking lot.
    If a live location is recieved, updates automatic recommendation handling.
    """
    async with UserManager(message.from_user) as s:
        lang = str(s.language)

        if message.location is None:
            return

        alert_triggered = s.bot_state == InteractionStates.PROXIMITY_TRIGGERED

        # If it is a live location and proximity alert was not triggered
        if (message.location.live_period is not None and
            message.location.live_period > 0 and
            not alert_triggered):
            # If it is the first time
            if not s.alert_set:
                # Set up automatic recommendation handling
                s.alert_set = True
                # Send a live location with proximity alert
                await bot.update_bot_location(
                    message.from_user,
                    s.user_type.live_pos,
                    message.chat.id
                )
                async with bot as api:
                    await api.send_message(
                        message.chat.id,
                        i18n.t("automatic.set", str(s.language))
                    )
            # Exit, as recommendation should not be sent now
            return

        # If automatic recommendation was setup but live location is no longer shared
        if s.alert_set and message.location.live_period is None:
            # Disable automatic recommendation handling
            s.alert_set = False
            await bot.update_bot_location(
                message.from_user,
                None,
                message.chat.id
            )
            async with bot as api:
                await api.send_message(
                    message.chat.id,
                    i18n.t("automatic.cancel", str(s.language))
                )
            return

        # If the proximity alert was triggered, reset alert
        if alert_triggered:
            s.alert_set = False
            s.bot_state = InteractionStates.IDLE

        parking_options = [
            p for p in await get_data(s.user_type)
            if not p.almost_full
        ]

        if len(parking_options) == 0:
            async with bot as api:
                await api.send_message(
                    message.chat.id,
                    i18n.t("error.all_full", str(s.language))
                )
                return

        # Only the best option (closest) is selected
        closest_park = sorted(
            [
                (
                    p,
                    haversine_distance(
                        message.location,
                        p.geo_pos
                    )
                )
                for p in parking_options
            ],
            key=lambda t: t[1]
        )[0][0]

        # Create inline button for navigation
        markup = util.quick_markup({
                i18n.t("recommended.nav_msg", lang):
                build_routing_data(closest_park.geo_pos, s.map_provider)
            },
            row_width=1
        )

        # Remove reply keyboard
        if not alert_triggered:
            await bot.update_reply_keyboard(message.chat.id)


        # Fetch map and send as photo
        nav_map = static_map(markers=[closest_park])
        async with request("GET", nav_map) as req:
            async with bot as api:
                await bot.update_inline_buttons(
                    message.from_user,
                    await api.send_photo(
                        message.chat.id,
                        await req.read(),
                        reply_markup=markup,
                        caption=i18n.t(
                            "recommended.msg",
                            locale=lang,
                            spot=closest_park.to_pretty(lang)
                        )
                    )
                )


@bot.api.message_handler(commands=["navigation"])
async def navigation_handler(message: types.Message):
    """
    Handler for the /navigation command.
    Displays inline buttons that can navigate to corresponding parking lots.
    """
    async with UserManager(message.from_user) as s:
        s.bot_state = InteractionStates.IDLE
        parking_spots = await get_data(s.user_type)
        parking_spots.sort(key=lambda p: p.free_spaces, reverse=True)
        parking_spots = [
            p for p in parking_spots if not p.is_inner_city
            and p.free_spaces > 0
        ]

        spot_btns = {
            i18n.t(
                "navigation.btn",
                locale=str(s.language),
                index=p.to_label(parking_spots.index(p) + 1),
                level=p.occupancy_level,
                free=p.free_spaces
            ) : build_routing_data(p.geo_pos, s.map_provider)
            for p in parking_spots
        }

        if len(spot_btns) == 0:
            async with bot as api:
                await api.send_message(
                    message.chat.id,
                    i18n.t("error.all_full", str(s.language))
                )
                return

        # Fetch map and send as photo
        nav_map = static_map(markers=parking_spots)
        async with request("GET", nav_map) as req:
            async with bot as api:
                await bot.update_inline_buttons(
                    message.from_user,
                    await api.send_photo(
                        message.chat.id,
                        await req.read(),
                        reply_markup=util.quick_markup(
                            spot_btns,
                            row_width=floor(sqrt(len(parking_spots)))
                        ),
                        caption=i18n.t("navigation.msg", str(s.language))
                    )
                )


@bot.api.message_handler(commands=["overview"])
async def overview_handler(message: types.Message):
    """
    Handler for the /overview command.
    Displays an overview of all car parks with their free spaces.
    """
    async with UserManager(message.from_user) as s:
        s.bot_state = InteractionStates.IDLE
        lang = str(s.language)
        all_spots = await get_data(s.user_type)

        sorted_spots = {"overview.campus" : [], "overview.city": []}
        for c in all_spots:
            (sorted_spots["overview.campus"],
             sorted_spots["overview.city"])[c.is_inner_city].append(c)

        for key, spots in sorted_spots.items():
            if len(spots) > 0:
                overview_msg = i18n.t(
                    f"{key}",
                    locale=lang,
                    msg="\n".join([c.to_pretty(lang, spots.index(c) + 1) for c in spots])
                )

                # Fetch map and send as photo
                nav_map = static_map(markers=spots)
                async with request("GET", nav_map) as req:
                    async with bot as api:
                        await api.send_photo(
                            message.chat.id,
                            await req.read(),
                            caption=overview_msg
                        )


@bot.api.message_handler(commands=["timer"])
async def timed_recommendation_handler(message: types.Message):
    """
    Handler for the /timer command.
    Sets a timer for when the user wants a parking recommendation.
    Optionally, a location can be specified for which to search nearby.
    """
    async with UserManager(message.from_user) as s:
        timer_old = s.timer
        s.timer = await parse_time_location(message.text, s.timer)

        # Message did not contain datetime
        if s.timer.date_time is None:
            # Recommendation was scheduled -> Cancelled
            if timer_old.date_time is not None:
                await bot.api.reply_to(
                    message,
                    i18n.t("timer.cancel", str(s.language))
                )
                await bot.update_timed_recommendation(message.from_user)
            # No recommendation was scheduled and no datetime was provided
            else:
                # Already asked -> Recommendation is not changed / cancelled
                if s.bot_state == InteractionStates.NEED_DATE_TIME:
                    await bot.api.reply_to(
                        message,
                        i18n.t("timer.set_cancel",str(s.language))
                    )
                    s.bot_state = InteractionStates.IDLE
                # Did not ask yet -> Ask for clarification
                else:
                    await bot.api.reply_to(
                        message,
                        i18n.t("timer.unknown", str(s.language))
                    )
                    s.bot_state = InteractionStates.NEED_DATE_TIME
        # Message did contain datetime -> Timer set / changed
        else:
            s.bot_state = InteractionStates.IDLE

            await bot.api.reply_to(message, i18n.t(
                (
                    "timer.set" if
                    s.timer.location == RoomNames.UNDEFINED else
                    "timer.loc_set"
                ),
                time=s.timer.date_time.strftime("%H:%M"),
                date=s.timer.date_time.strftime("%-d.%-m."),
                loc=i18n.t(repr(s.timer.location), str(s.language)),
                locale=str(s.language)
            ))

            await bot.update_timed_recommendation(message.from_user)


@bot.api.message_handler(content_types="text")
async def free_text_handler(message: types.Message):
    """
    Handles free inputs from the user, such as text messages (or audio?).
    Attempts to map the input to one of the available commands and executes it.
    If not command could be detected, a clarification message is sent instead.
    """
    async with UserManager(message.from_user) as s:
        # Skip free text if we are waiting for a time input
        if s.bot_state == InteractionStates.NEED_DATE_TIME:
            await timed_recommendation_handler(message)
            return

        parsed = await parse_command(message.text)
        match parsed:
            case BotCommands.NAVIGATION:
                await navigation_handler(message)
            case BotCommands.TIMER:
                await timed_recommendation_handler(message)
            case BotCommands.RECOMMEND:
                await recommend_handler(message)
            case BotCommands.OVERVIEW:
                await overview_handler(message)
            case BotCommands.AUTOMATIC:
                await automatic_handler(message)
            case _:
                await bot.api.reply_to(
                    message,
                    formatting.format_text(
                        i18n.t("error.command_unknown", str(s.language)),
                        await bot.help_message(str(s.language))
                    ),
                    parse_mode="Markdown"
                )


@bot.api.message_handler(content_types=["voice"])
async def voice_input_handler(message: types.Message):
    """
    Wrapper handler for voice input being recieved as voice message
    """
    async with UserManager(message.from_user) as s:
        processing = await bot.api.reply_to(
            message,
            i18n.t("voice.processing", str(s.language))
        )

        recieved_text = await transcripe(message)
        message.text = recieved_text

        # Echo so the user knows what was transcribed
        await bot.api.edit_message_text(
            (
                i18n.t("voice.not_understood", str(s.language)) if
                recieved_text is None else
                formatting.format_text(
                    i18n.t("voice.echo_msg", str(s.language)),
                    formatting.mbold(recieved_text)
                )
            ),
            processing.chat.id,
            processing.message_id,
            parse_mode="Markdown",
        )

        await free_text_handler(message)
