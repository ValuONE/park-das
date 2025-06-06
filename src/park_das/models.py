from dataclasses import dataclass
from typing import Optional

import aiosqlite

from telebot.util import quick_markup
from telebot.types import Location, User

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
    
        Returns:
            tuple[float, float]: A tuple containing the latitude and longitude of the car park.
        """
        return self.name.get_pos()

    def emojify_status(self) -> str:
        ratio = self.free_spaces / self.total_spaces
        if ratio > 0.25:
            return "✅"
        if 0.1 <= ratio < 0.25:
            return "⚠️"
        if 0.0 < ratio < 0.1:
            return "🛑"
        return "⛔️"

    def to_pretty(self):
        """
        Formats a car park's information into a string.
    
        Args:
            park (CarPark): The car park to format.
    
        Returns:
            str: A formatted string containing the car park's name, free spaces and a status icon.
        """
        return (f"{self.name.value}: {self.free_spaces} frei | "
                f"{self.emojify_status()}\n")

@dataclass
class UserSettings:
    language: UserLanguage = UserLanguage.UNDEFINED
    map_provider: MapProvider = MapProvider.UNDEFINED
    user_type: UserType = UserType.UNDEFINED
    last_location: Optional[Location] = None
    inline_buttons: Optional[InlineButtons] = None

    def __str__(self) -> str:
        return "\n".join(
            [
                f"Gewählte Sprache:\t\t{str(self.language)}",
                f"Karten Präferenz:\t\t{str(self.map_provider)}",
                f"Nutzer Art:\t\t{str(self.user_type)}"
            ]
        )

    @classmethod
    def markup_buttons(cls):
        return quick_markup(
            {
                "Sprache": {"callback_data" : "user_language"},
                "Kartenanbieter": {"callback_data" : "map_provider"},
                "Nutzertyp": {"callback_data" : "user_type"}
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
        self._user = user

    async def _load_settings(self) -> UserSettings:
        if self._user is None:
            return UserSettings()

        async with aiosqlite.connect(UserSettingsManager.DB_PATH) as con:
            await con.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER PRIMARY KEY,
                    language INTEGER NOT NULL,
                    map_provider INTEGER NOT NULL,
                    user_type INTEGER NOT NULL,
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
