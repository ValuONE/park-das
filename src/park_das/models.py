from dataclasses import dataclass
from typing import Optional

import aiosqlite
import i18n

from telebot.util import quick_markup
from telebot.types import Location, User, InlineKeyboardMarkup

from .constants import CarParkNames, UserLanguage, UserType, MapProvider


@dataclass
class InlineButtons:
    chat_id: int
    message_id: int


@dataclass
class CarPark:
    """
    Represents a car park with a name and the number of available spaces.
    
    Attributes:
        name (CarParkNames): The name of the car park, based on the CarParkNames enum.
        free_spaces (int): The current number of available parking spaces.
        total_spaces (int): The total number of available parking spaces.
    """
    name: CarParkNames
    free_spaces: int
    total_spaces: int

    def get_pos(self) -> Location:
        """
        Returns the geographic position (latitude, longitude) of the car park.

        :return: A telegram location containing the latitude and longitude of the car park.
        """
        return self.name.get_pos()

    def occupancy_level(self, as_emoji = True) -> str:
        """
        Get a visual representation of the current occupancy level

        :param as_emoji: If set, the representation will be emoji
        :return: Either an emoji or a color
        """
        ratio = self.free_spaces / self.total_spaces
        if ratio > 0.25:
            return "✅" if as_emoji else "green"
        if 0.1 <= ratio < 0.25:
            return "⚠️" if as_emoji else "yellow"
        if 0.0 < ratio < 0.1:
            return "🛑" if as_emoji else "red"
        return "⛔️" if as_emoji else "gray"

    def to_pretty(self, lang : str) -> str:
        """
        Formats a car park's information into a string.

        :return: A formatted string containing the car park's name, free spaces and a status icon.
        """
        return i18n.t("strings.overview_msg",
                      name = self.name.value,
                      free = self.free_spaces,
                      occupancy = self.occupancy_level(),
                      locale=lang)

@dataclass
class UserSettings:
    language: UserLanguage = UserLanguage.UNDEFINED
    map_provider: MapProvider = MapProvider.UNDEFINED
    user_type: UserType = UserType.UNDEFINED
    last_location: Optional[Location] = None
    inline_buttons: Optional[InlineButtons] = None

    def __str__(self) -> str:
        lang = str(self.language)
        return "\n".join(
            [
                i18n.t("settings.options.language_curr",
                       locale=lang,
                       curr=i18n.t(repr(self.language), lang)),
                i18n.t("settings.options.mapprovider_curr",
                       locale=lang,
                       curr=i18n.t(repr(self.map_provider), lang)),
                i18n.t("settings.options.usertype_curr",
                       locale=lang,
                       curr=i18n.t(repr(self.user_type), lang))
            ]
        )

    @classmethod
    def markup_buttons(cls, lang : str) -> InlineKeyboardMarkup:
        """
        Creates inline buttons to attach to a message

        :return: A predefined set of inline buttons
        """
        return quick_markup(
            {
                i18n.t("settings.options.language", lang): {"callback_data" : "user_language"},
                i18n.t("settings.options.mapprovider", lang): {"callback_data" : "map_provider"},
                i18n.t("settings.options.usertype", lang): {"callback_data" : "user_type"}
            },
            row_width=1
        )


class UserSettingsManager:
    DB_PATH = "settings.db"

    _instance = None
    _refs = {}

    def __new__(cls, user: User | None = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, user : User | None):
        """
        Opens database to access user information

        :param user: Telegram user to access
        """
        self._user = user

    async def _load_settings(self) -> UserSettings:
        if self._user is None:
            return UserSettings()

        async with aiosqlite.connect(UserSettingsManager.DB_PATH) as con:
            await con.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT NOT NULL,
                    map_provider TEXT NOT NULL,
                    user_type TEXT NOT NULL,
                    longitude REAL,
                    latitude REAL,
                    chat_id INTEGER,
                    message_id INTEGER
                )
                """
            )

            async with con.execute(
                """
                SELECT language, map_provider, user_type, longitude, latitude, chat_id, message_id
                FROM settings
                WHERE user_id = ?
                """,
                (
                    self._user.id,
                )
            ) as cursor:
                result = await cursor.fetchone()
                return UserSettings(
                    language=UserLanguage(result[0]),
                    map_provider=MapProvider(result[1]),
                    user_type=UserType(result[2]),
                    last_location=Location(result[3], result[4])
                        if result[3] is not None else None,
                    inline_buttons=InlineButtons(result[5], result[6])
                        if result[5] is not None else None
                ) if result is not None else UserSettings()

    async def __aenter__(self) -> UserSettings:
        if self._user is None:
            return UserSettings()


        if self._user.id not in self._refs:
            self._refs[self._user.id] = await self._load_settings()

        return self._refs[self._user.id]

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool:
        if self._user is None:
            return False

        async with aiosqlite.connect(UserSettingsManager.DB_PATH) as con:
            settings = self._refs[self._user.id]
            await con.execute(
                """
                INSERT OR REPLACE INTO settings
                (user_id, language, map_provider, user_type,
                longitude, latitude, chat_id, message_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self._user.id,
                    settings.language.value,
                    settings.map_provider.value,
                    settings.user_type.value,
                    settings.last_location.longitude if settings.last_location else None,
                    settings.last_location.latitude if settings.last_location else None,
                    settings.inline_buttons.chat_id if settings.inline_buttons else None,
                    settings.inline_buttons.message_id if settings.inline_buttons else None
                )
            )
            await con.commit()

        return True
