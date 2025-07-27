from math import sqrt, floor
from json import loads

from aiofiles import open as aiopen
from aiohttp import request

from telebot import types, util, formatting

import aioschedule
import i18n

from .models import BotMessage

from .scrapper import get_data
from .models import UserSettingsManager, UserSettings, RecommendationTimer
from .constants import MapProvider, UserType, UserLanguage, OutputType, InteractionStates
from .util import haversine_distance, build_routing_data, static_map
from .message_analyser import parse_command, BotCommands, parse_time_location
from .voice_support import transcripe

from .bot import bot

@bot.api.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    """
    Handler for the /start command.
    Creates user settings for new users, sends help message.
    """
    async with bot as api:
        async with UserSettingsManager(message.from_user) as s:
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
        async with UserSettingsManager(message.from_user) as s:
            s.bot_state = InteractionStates.IDLE
            await api.send_message(
                message.chat.id,
                await bot.help_message(str(s.language)),
                parse_mode="Markdown"
            )

@bot.api.callback_query_handler(
    func=lambda cb: cb.data and (
        cb.data in {"user_language", "map_provider", "user_type", "output_type", "back"}
        or (cb.data.startswith("{") and cb.data.endswith("}"))
    )
)
async def handle_settings_callback(cb: types.CallbackQuery):
    async with UserSettingsManager(cb.from_user.id) as s:
        lang = str(s.language)
        api = bot.api
        msg = cb.message
        data = cb.data or ""

        # Nur reagieren, wenn es unsere Settings-Message ist
        if not s.inline_buttons.exists or msg.message_id != s.inline_buttons.message_id:
            return await api.answer_callback_query(cb.id)

        # --- 1) Menü-Buttons ---
        if data in ("user_language", "map_provider", "user_type", "output_type", "back"):
            markup_map = {
                "user_language": UserLanguage.markup_buttons,
                "map_provider":  MapProvider.markup_buttons,
                "user_type":     UserType.markup_buttons,
                "output_type":   OutputType.markup_buttons,
                "back":          UserSettings.markup_buttons,
            }
            await api.edit_message_reply_markup(
                msg.chat.id, msg.message_id,
                reply_markup=markup_map[data](lang)
            )
            return await api.answer_callback_query(cb.id)

        # --- 2) JSON-Buttons (Wert setzen) ---
        if data.startswith("{") and data.endswith("}"):
            try:
                update = loads(data)
            except ValueError:
                return await api.answer_callback_query(cb.id, "Ungültige Daten!", show_alert=True)

            old_output = s.output_type

            if UserLanguage.__name__ in update:
                s.language = UserLanguage(update[UserLanguage.__name__])
                lang = str(s.language)
            if MapProvider.__name__ in update:
                s.map_provider = MapProvider(update[MapProvider.__name__])
            if UserType.__name__ in update:
                s.user_type = UserType(update[UserType.__name__])
            if OutputType.__name__ in update:
                s.output_type = OutputType(update[OutputType.__name__])

            # OutputType-Wechsel speziell behandeln
            if old_output != s.output_type:

                # alte Settings-Message weg
                try:
                    await api.delete_message(msg.chat.id, msg.message_id)

                # pylint: disable=bare-except
                except Exception:
                    pass

                # ggf. alte Voice-Vorschau löschen
                if getattr(s, "settings_voice_id", None):
                    try:
                        await api.delete_message(msg.chat.id, s.settings_voice_id)

                    # pylint: disable=bare-except
                    except Exception:
                        pass
                    s.settings_voice_id = None

                if s.output_type == OutputType.VOICE:
                    new_msg = await api.send_message(
                        msg.chat.id,
                        str(s),
                        reply_markup=UserSettings.markup_buttons(lang),
                        voice_only=True
                    )
                    s.settings_voice_id = new_msg.message_id
                else:
                    new_msg = await api.send_message(
                        msg.chat.id,
                        str(s),
                        reply_markup=UserSettings.markup_buttons(lang)
                    )

                s.inline_buttons = BotMessage(new_msg.chat.id, new_msg.message_id)
                return await api.answer_callback_query(cb.id)

            # Kein Wechsel → Text & Buttons einfach editieren
            await api.edit_message_text(
                str(s),
                msg.chat.id,
                msg.message_id,
                reply_markup=UserSettings.markup_buttons(lang),
                parse_mode="Markdown"
            )
            return await api.answer_callback_query(cb.id)

        # --- 3) Fallback ---
        return await api.answer_callback_query(cb.id, "Unbekannter Callback", show_alert=True)

@bot.api.message_handler(commands=["settings"])
async def settings_handler(message: types.Message):
    """
    Handler for the /settings command
    Displays current settings in text message and inline buttons to adjust settings.
    """
    async with UserSettingsManager(message.from_user) as s:
        s.bot_state = InteractionStates.IDLE
        async with bot as api:
            sent = await api.send_message(
                message.chat.id,
                str(s),
                reply_markup=UserSettings.markup_buttons(str(s.language))
            )

            await bot.update_inline_buttons(message.from_user, sent)


@bot.api.message_handler(commands=["automatic"])
async def automatic_handler(message: types.Message):
    """
    Handler for the /automatic command.
    Sends a tutorial for how to activate the functionality.
    """
    async with UserSettingsManager(message.from_user) as s:
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
    async with UserSettingsManager(message.from_user) as s:
        s.bot_state = InteractionStates.IDLE

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
    async with UserSettingsManager(message.from_user) as s:
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
    Receives user's location and returns sorted car parks.
    """
    async with UserSettingsManager(message.from_user) as s:
        lang = str(s.language)

        if message.location is None:
            return

        alert_triggered = s.bot_state == InteractionStates.PROXIMITY_TRIGGERED

        # If live location is activated for the first time
        if (message.location.live_period is not None and
            message.location.live_period > 0 and
            not alert_triggered):
            # Ensure it is only set once
            if not s.alert_set:
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
            return

        # Remove alert if live location is no longer shared
        if s.alert_set and message.location.live_period is None:
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

        if alert_triggered:
            s.alert_set = False
            s.bot_state = InteractionStates.IDLE

        options = [
            p for p in await get_data(s.user_type)
            if not p.almost_full
        ]

        if len(options) == 0:
            async with bot as api:
                await api.send_message(
                    message.chat.id,
                    i18n.t("error.all_full", str(s.language))
                )
                return

        closest_park = sorted(
            [
                (
                    p,
                    haversine_distance(
                        message.location,
                        p.geo_pos
                    )
                )
                for p in options
            ],
            key=lambda t: t[1]
        )[0][0]

        # Determine the map provider to use for building URLs
        markup = util.quick_markup({
                i18n.t("recommended.nav_msg", lang):
                build_routing_data(closest_park.geo_pos, s.map_provider)
            },
            row_width=1
        )

        # Remove reply keyboard
        if not alert_triggered:
            await bot.update_reply_keyboard(message.chat.id)

        async with bot as api:
            await bot.update_inline_buttons(
                message.from_user,
                await api.send_message(
                    message.chat.id,
                    i18n.t(
                        "recommended.msg",
                        locale=lang,
                        spot=closest_park.to_pretty(lang)
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
                sent = await api.send_photo(
                    message.chat.id,
                    await req.read(),
                    reply_markup=util.quick_markup(
                        spot_btns,
                        row_width=floor(sqrt(len(parking_spots)))
                    ),
                    caption=i18n.t(
                        "navigation.msg",
                        str(s.language)
                    )
                )

                await bot.update_inline_buttons(
                    message.from_user,
                    sent
                )

                @bot.api.callback_query_handler(lambda c : c.message.message_id == sent.message_id)
                async def handle_navigation_callback(cb : types.CallbackQuery):
                    await api.answer_callback_query(
                        cb.id,
                        formatting.format_text(
                            i18n.t("error.mapprovider_not_set", str(s.language))
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
async def timing_handler(message: types.Message):
    """
    Handler for the /timer command.
    Sets a timer for when the user needs a parking recommendation.
    Optionally, a location can be specified to search for a spot nearby.
    """
    async with UserSettingsManager(message.from_user) as s:
        result = await parse_time_location(message.text)
        # If no time was supplied, ask for it
        if result is None or result.time is None:
            # If no date time was given
            if s.bot_state == InteractionStates.NEED_DATE_TIME:
                # Potentially cancel the reminder..
                if result.cancel:
                    await bot.api.reply_to(
                        message,
                        i18n.t("timer.cancel", str(s.language))
                    )
                    aioschedule.clear(message.from_user.id) # type: ignore
                    s.timer = RecommendationTimer()
                # .. or inform user that nothing was changed
                else:
                    await bot.api.reply_to(
                        message,
                        i18n.t(
                            (
                                "timer.set_cancel" if
                                not s.timer.exists else
                                "timer.set_already_cancel"
                            ),
                            str(s.language))
                    )
                s.bot_state = InteractionStates.IDLE
                return
            # Potentially warn user that a timer was already set
            if s.timer.exists:
                await bot.api.reply_to(
                    message,
                    i18n.t(
                        (
                            "timer.set_already" if
                            not s.timer.with_location else
                            "timer.loc_set_already"
                        ),
                        time=s.timer.time,
                        date=s.timer.date,
                        loc=s.timer.loc,
                        locale=str(s.language)
                    )
                )
            else:
                await bot.api.reply_to(
                    message,
                    i18n.t("timer.unknown", str(s.language))
                )
            s.bot_state = InteractionStates.NEED_DATE_TIME
        else:
            s.bot_state = InteractionStates.IDLE

            await bot.api.reply_to(message, i18n.t(
                (
                    "timer.set" if
                    result.location is None else
                    "timer.loc_set"
                ),
                time=result.time.strftime("%H:%M"),
                date=result.time.strftime("%-d.%-m."),
                loc=result.location,
                locale=str(s.language)
            ))

            # Store for later
            s.timer = RecommendationTimer(
                result.time.strftime("%H:%M"),
                result.time.strftime("%-d.%-m."),
                result.location
            )

            # Possibly remove existing reminder
            aioschedule.clear(message.from_user.id) # type: ignore
            # Determine day (-> only at most one week in the future!)
            day_of_week = result.time.strftime("%A").lower()
            # pylint: disable=no-member
            aioschedule.every().on(day_of_week).at( # type: ignore
                result.time.strftime("%H:%M")
            ).do(recommend_on_timer, message=message).tag(message.from_user.id) # type: ignore
            # pylint: enable=no-member


async def recommend_on_timer(message: types.Message):
    """
    Handler for set timers triggering.
    Activates navigation command when running out.
    """
    async with UserSettingsManager(message.from_user) as s:
        aioschedule.clear(message.from_user.id) # type: ignore
        s.timer = RecommendationTimer()
        await navigation_handler(message)


@bot.api.message_handler(content_types="text")
async def free_text_handler(message: types.Message):
    """
    Handles free inputs from the user, such as text messages (or audio?).
    Attempts to map the input to one of the available commands and executes it.
    If not command could be detected, a clarification message is sent instead.
    """
    async with UserSettingsManager(message.from_user) as s:
        # Skip free text if we are waiting for a time input
        if s.bot_state == InteractionStates.NEED_DATE_TIME:
            await timing_handler(message)
            return

        parsed = await parse_command(message.text)
        match parsed:
            case BotCommands.NAVIGATION:
                await navigation_handler(message)
            case BotCommands.TIMER:
                await timing_handler(message)
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
    async with UserSettingsManager(message.from_user) as s:
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
