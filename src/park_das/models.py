import sqlite3
from dataclasses import dataclass
from typing import Optional

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


@dataclass
class UserSettings:
    language: UserLanguage
    map_provider: MapProvider
    user_type: UserType
    last_location: Optional[Location] = None
    inline_button: Optional[InlineButtons] = None

    def __str__(self) -> str:
        return "\n".join(
            [
                f"Gewählte Sprache:\t\t{str(self.language)}",
                f"Karten Präferenz:\t\t{str(self.map_provider)}",
                f"Nutzer Art:\t\t{str(self.user_type)}"
            ]
        )


class UserSettingsManager:
    DB_PATH = "settings.db"

    def __init__(self, user: User | None):
        self._user_id = user.id if user else 0
        self._conn = sqlite3.connect(UserSettingsManager.DB_PATH)
        self._cursor = self._conn.cursor()
        self._conn.execute(
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

    @property
    def settings(self) -> UserSettings:
        result = self._cursor.execute(
            """
            SELECT language, map_provider, user_type, longitude, latitude, chat_id, message_id
            FROM settings
            WHERE user_id = ?
            """,
            (
                self._user_id,
            )
        )
        result = self._cursor.fetchone()
        if result is not None:
            return UserSettings(
                language=UserLanguage(result[0]),
                map_provider=MapProvider(result[1]),
                user_type=UserType(result[2]),
                last_location=Location(result[3], result[4])
                    if result[3] is not None else None,
                inline_button=InlineButtons(result[5], result[6])
                    if result[5] is not None else None
            )
        return UserSettings(
            language=UserLanguage.UNDEFINED,
            map_provider=MapProvider.UNDEFINED,
            user_type=UserType.UNDEFINED,
            last_location=None,
            inline_button=None
        )

    @settings.setter
    def settings(self, settings: UserSettings):
        if self._user_id == 0:
            return

        self._cursor.execute(
            """
            INSERT OR REPLACE INTO settings
            (user_id, language, map_provider, user_type, longitude, latitude, chat_id, message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self._user_id,
                settings.language.value,
                settings.map_provider.value,
                settings.user_type.value,
                settings.last_location.longitude if settings.last_location else None,
                settings.last_location.latitude if settings.last_location else None,
                settings.inline_button.chat_id if settings.inline_button else None,
                settings.inline_button.message_id if settings.inline_button else None
            )
        )
        self._conn.commit()

    @settings.deleter
    def settings(self):
        if self._user_id == 0:
            return

        self._cursor.execute(
            """
            DELETE FROM settings WHERE user_id = ?
            """,
            (
                self._user_id,
            )
        )
        self._conn.commit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._cursor.close()
        if isinstance(exc_value, Exception):
            self._conn.rollback()
        else:
            self._conn.commit()
        self._conn.close()
