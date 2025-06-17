import os

from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_filters import StateFilter
from telebot.asyncio_storage import StateMemoryStorage
from telebot.states.asyncio.middleware import StateMiddleware
from telebot import types, formatting
# necessary for state parameter in handlers.

import i18n

from .models import UserSettingsManager, InlineButtons

class ParkBot:

    def __init__(self) -> None:
        try:
            token = os.environ["TELEGRAM_TOKEN"]
        except KeyError as e:
            raise ValueError("TELEGRAM_TOKEN environment variable is not set or is empty.") from e

        data = StateMemoryStorage()
        self._bot = AsyncTeleBot(token, state_storage=data)

    async def setup_bot(self):
        """
        Creates bot commands, does all initialization
        """
        self.api.add_custom_filter(StateFilter(self.api))
        self.api.setup_middleware(StateMiddleware(self.api))
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
                        "live",
                        i18n.t("commands.live", lang)
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

    async def update_inline_buttons(self, user : types.User | None, message : types.Message):
        """
        Ensures only one set of inline buttons is present.

        :param user: User the inline buttons are sent to
        :param message: New message containing inline buttons
        """
        async with UserSettingsManager(user) as s:
            if s.inline_buttons is not None:
                await self.api.delete_message(s.inline_buttons.chat_id,
                                              s.inline_buttons.message_id)
            s.inline_buttons = InlineButtons(message.chat.id, message.message_id)

    async def help_message(self, user: types.User | None) -> str:
        """
        Generates help message in the user's selected language

        :param user: User for whom to generate the message
        :return: Formatted, translated help message
        """
        async with UserSettingsManager(user) as s:
            cmds = await bot.api.get_my_commands(scope=None, language_code=str(s.language))
            cmds_str = "\n".join([f"/{cmd.command} : {cmd.description}" for cmd in cmds])
            return formatting.format_text(
                formatting.mbold(f"{i18n.t('strings.help_msg', str(s.language))}:"),
                cmds_str
            )
        return ""

# Global instance to be used when doing anything with the API
bot = ParkBot()
