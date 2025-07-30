import os

from telebot.async_telebot import AsyncTeleBot
from telebot import types, formatting

import i18n

from .models import UserManager, BotMessage

class ParkBot:

    def __init__(self) -> None:
        try:
            token = os.environ["TELEGRAM_TOKEN"]
        except KeyError as e:
            raise ValueError("TELEGRAM_TOKEN environment variable is not set or is empty.") from e

        self._bot = AsyncTeleBot(token)

    async def setup_bot(self):
        """
        Creates bot commands, does all initialization
        """
        await self.api.delete_my_commands()
        for lang in i18n.get("available_locales"):
            await self.api.set_my_commands(
                [
                    types.BotCommand(
                        "start",
                        i18n.t("commands.start", lang)
                    ),
                    types.BotCommand(
                        "help",
                        i18n.t("commands.help", lang)
                    ),
                    types.BotCommand(
                        "settings",
                        i18n.t("commands.settings", lang)
                    ),
                    types.BotCommand(
                        "overview",
                        i18n.t("commands.overview", lang)
                    ),
                    types.BotCommand(
                        "automatic",
                        i18n.t("commands.automatic", lang)
                    ),
                    types.BotCommand(
                        "recommend",
                        i18n.t("commands.recommend", lang)
                    ),
                    types.BotCommand(
                        "navigation",
                        i18n.t("commands.navigation", lang)
                    ),
                    types.BotCommand(
                        "timer",
                        i18n.t("commands.timer", lang)
                    )
                ],
                language_code=lang
            )

    async def __aenter__(self) -> AsyncTeleBot:
        return self._bot

    async def __aexit__(self, exception_type, exception_val, trace):
        return True

    @property
    def api(self) -> AsyncTeleBot:
        """
        Bot API accessor

        :return: The telegram bot API
        """
        return self._bot

    async def update_inline_buttons(self, user: types.User | int | None, sent: types.Message):
        """
        Ensures only one set of inline buttons is present.

        :param user: User the message was sent to
        :param sent: Message containing inline buttons
        """
        async with UserManager(user) as s:
            if s.inline_buttons.exists:
                try:
                    await self.api.delete_message(
                        s.inline_buttons.chat_id, # type: ignore
                        s.inline_buttons.message_id # type: ignore
                    )
                except Exception: # pylint: disable=broad-exception-caught
                    pass
            s.inline_buttons = BotMessage(
                sent.chat.id,
                sent.message_id
            )

    async def update_reply_keyboard(self, chat_id: int):
        """
        Ensures reply keyboard is only available when necessary.

        :param chat_id: Chat containing reply keyboard
        """
        sent = await self.api.send_message(
            chat_id,
            "⏳ ... ⌛️",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await self.api.delete_message(
            sent.chat.id,
            sent.message_id
        )

    async def update_bot_location(
        self,
        user: types.User | int | None,
        location: types.Location | None,
        chat_id: int
    ):
        """
        Ensures bot shares only one live location.

        :param user: User the location is sent to
        :param location: Location of the bot or None if it should be removed
        :param chat_id: Chat the location belongs to
        """
        async with UserManager(user) as s:
            if location is not None:
                if s.auto_alert.exists:
                    try:
                        sent = await self.api.edit_message_live_location(
                            location.latitude,
                            location.longitude,
                            chat_id=s.auto_alert.chat_id,
                            message_id=s.auto_alert.message_id,
                            live_period=location.live_period,
                            proximity_alert_radius=location.proximity_alert_radius
                        )
                    except Exception: # pylint: disable=broad-exception-caught
                        sent = await self.api.send_location(
                            chat_id,
                            location.latitude,
                            location.longitude,
                            live_period=location.live_period,
                            proximity_alert_radius=location.proximity_alert_radius,
                            disable_notification=True
                        )
                else:
                    sent = await self.api.send_location(
                        chat_id,
                        location.latitude,
                        location.longitude,
                        live_period=location.live_period,
                        proximity_alert_radius=location.proximity_alert_radius,
                        disable_notification=True
                    )
                s.auto_alert = BotMessage(
                    sent.chat.id,
                    sent.message_id
                )
            else:
                try:
                    to_delete = await self.api.stop_message_live_location(
                        s.auto_alert.chat_id,
                        s.auto_alert.message_id
                    )
                    await self.api.delete_message(
                        to_delete.chat.id,
                        to_delete.message_id
                    )
                except Exception: # pylint: disable=broad-exception-caught
                    pass
                finally:
                    s.auto_alert = BotMessage()
                    s.alert_set = False

    async def help_message(self, language: str) -> str:
        """
        Generates help message in the user's selected language

        :param user: User for whom to generate the message
        :return: Formatted, translated help message
        """
        cmds = await bot.api.get_my_commands(scope=None, language_code=language)
        cmds_str = "\n".join([f"/{cmd.command} : {cmd.description}" for cmd in cmds])
        return formatting.format_text(
            formatting.mbold(i18n.t("help.msg", language)),
            cmds_str
        )

# Global instance to be used when doing anything with the API
bot = ParkBot()
