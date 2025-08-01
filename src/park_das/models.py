from json import loads, dumps
from enum import Enum
from typing import List
from datetime import datetime
from dataclasses import dataclass, fields, is_dataclass
from sqlite3 import PARSE_DECLTYPES

import aiosqlite

from telebot.util import quick_markup
from telebot.types import Location, User, InlineKeyboardMarkup

import i18n

from .constants import  ParkingLotNames, UserLanguage, UserType,\
                        MapProvider, OutputType, InteractionStates, PARKING_LOT_LOCATIONS,\
                        RoomNames, ROOM_LOCATIONS, Callbacks, Settings

@dataclass
class ParkingLot:
    """
    Represents a parking lot with a name and the number of available spaces.
    
    Attributes:
        _code_name: The name of the parking lot, based on the ParkingLotNames enum.
        free_spaces: The current number of available parking spaces.
        total_spaces: The total number of available parking spaces.
        is_visitor: Flag whether this is a visitor parking spot.
    """
    _code_name: ParkingLotNames
    free_spaces: int
    total_spaces: int
    is_visitor: bool

    _RATIO_FREE = 0.25
    _RATIO_CRITICAL = 0.1
    _RATIO_FULL = 0.0
    _SPACES_FREE = 50
    _SPACES_CRITICAL = 25

    def __eq__(self, value: object) -> bool:
        """
        Test for equality between parking spots

        :param value: Other parking spot
        :return: True if name is same
        """
        if isinstance(value, ParkingLot):
            return self._code_name == value._code_name
        if isinstance(value, ParkingLotNames):
            return self._code_name == value
        return False

    def __str__(self) -> str:
        """
        Returns name of parking area

        :return: Parking area name
        """
        return str(self._code_name)

    @property
    def is_inner_city(self) -> bool:
        """
        Returns whether parking area is in the city

        :return: Flag if parking spot is in the city
        """
        return str(self._code_name).startswith("M")

    @property
    def geo_pos(self) -> Location:
        """
        Returns the geographic position (latitude, longitude) of the parking lot.

        :return: A telegram location containing the latitude and longitude of the parking lot.
        """
        return PARKING_LOT_LOCATIONS[self._code_name]

    @property
    def almost_full(self) -> bool:
        """
        Determines if parking spot is basically full already

        :return: Flag whether spot is almost full
        """
        ratio = self.free_spaces / self.total_spaces
        return ratio < self._RATIO_CRITICAL

    @property
    def occupancy_level(self) -> str:
        """
        Get a visual representation of the current occupancy level

        :return: Emoji that signifies occupancy level
        """
        ratio = self.free_spaces / self.total_spaces
        if (ratio > self._RATIO_FREE or
            self.free_spaces > self._SPACES_FREE):
            return "✅"
        if (self._RATIO_CRITICAL <= ratio < self._RATIO_FREE or
            self.free_spaces > self._SPACES_CRITICAL):
            return "⚠️"
        if self._RATIO_FULL < ratio < self._RATIO_CRITICAL:
            return "🛑"
        return "⛔️"

    def to_label(self, index: int | None) -> str:
        """
        Index (0, ...) to char (1 ... 9, A ... Z)

        :param index: Index of spot in list
        :return: Char to be used as label
        """
        return ("" if index is None else
                chr(48 + index) if index < 10 else chr(55 + index))

    def to_pretty(self, lang: str, index: int | None = None) -> str:
        """
        Formats a parking lot's information into a string.

        :return: A formatted string containing the parking lot's name,\
                 free spaces and a status icon.
        """
        return i18n.t(
            ("overview.single"
             if index is None else
             "overview.multiple"),
            index=self.to_label(index),
            name=self._code_name.value,
            free=self.free_spaces,
            occupancy=self.occupancy_level,
            locale=lang
        )

    # https://developers.google.com/maps/documentation/maps-static/start#Markers
    def to_map_marker(self, index : int) -> str:
        """
        Generates a formatted marker for the google maps api

        :param index: Index is used as label
        :return: Marker as formatted string
        """
        loc = self.geo_pos
        ratio = self.free_spaces / self.total_spaces

        if (ratio > self._RATIO_FREE or
            self.free_spaces > self._SPACES_FREE):
            col = "green"
            size = ""
        elif (self._RATIO_CRITICAL <= ratio < self._RATIO_FREE or
            self.free_spaces > self._SPACES_CRITICAL):
            col = "yellow"
            size = "mid"
        elif self._RATIO_FULL < ratio < self._RATIO_CRITICAL:
            col = "red"
            size = "mid"
        else:
            col = "gray"
            size = "tiny"

        return (
            f"color:{col}|"
            f"label:{self.to_label(index)}|"
            f"size:{size}|"
            f"scale:2|"
            f"{loc.latitude},{loc.longitude}"
        )


@dataclass
class Room:
    """
    Represents a location with a name.
    
    Attributes:
        _code_name: The name of the location, based on the RoomNames enum.
    """
    _code_name : RoomNames

    def __eq__(self, value: object) -> bool:
        """
        Test for equality between locations

        :param value: Other location
        :return: True if name is same
        """
        if isinstance(value, Room):
            return self._code_name == value._code_name
        if isinstance(value, RoomNames):
            return self._code_name == value
        return False

    def __str__(self) -> str:
        """
        Returns name of location

        :return: Room / building name
        """
        return str(self._code_name)

    @property
    def geo_pos(self) -> Location:
        """
        Returns the geographic position (latitude, longitude) of the location.

        :return: A telegram location containing the latitude and longitude of the location.
        """
        return ROOM_LOCATIONS[self._code_name]


@dataclass
class BotMessage:
    chat_id : int | None = None
    message_id : int | None = None

    @property
    def exists(self) -> bool:
        return self.chat_id is not None and self.message_id is not None


@dataclass
class TimedRecommendation:
    date_time: datetime | None = None
    location: RoomNames = RoomNames.UNDEFINED

    @property
    def with_location(self) -> bool:
        return self.location is not None


@dataclass
class UserData:
    language: UserLanguage = UserLanguage.UNDEFINED
    map_provider: MapProvider = MapProvider.UNDEFINED
    user_type: UserType = UserType.UNDEFINED
    output_type: OutputType = OutputType.UNDEFINED
    bot_state: InteractionStates = InteractionStates.IDLE
    inline_buttons: BotMessage = BotMessage()
    auto_alert: BotMessage = BotMessage()
    alert_set: bool = False
    timer: TimedRecommendation = TimedRecommendation()
    settings_voice_id: int | None = None

    def __str__(self) -> str:
        lang = str(self.language)
        return "\n".join(
            [
                i18n.t(
                    "settings.options.userlanguage_curr",
                    locale=lang,
                    curr=i18n.t(
                        repr(self.language),
                        lang
                    )
                ),
                i18n.t(
                    "settings.options.mapprovider_curr",
                    locale=lang,
                    curr=i18n.t(
                        repr(self.map_provider),
                        lang
                    )
                ),
                i18n.t(
                    "settings.options.usertype_curr",
                    locale=lang,
                    curr=i18n.t(
                        repr(self.user_type),
                        lang
                    )
                ),
                i18n.t(
                    "settings.options.outputtype_curr",
                    locale=lang,
                    curr=i18n.t(
                        repr(self.output_type),
                        lang
                    )
                )
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
                i18n.t("settings.options."+s.name.lower(), lang): {
                    "callback_data" : dumps({
                        "type": Callbacks.SETTINGS_SELECT,
                        "select": s.name
                    })
                }
                for s in Settings
            },
            row_width=1
        )

    @classmethod
    def adapt(cls, settings: "UserData") -> bytes:
        """Convert UserSettings to bytes using Enum values and recursive dataclass handling."""
        def serialize(obj):
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, datetime):
                return obj.isoformat(timespec='minutes')
            if is_dataclass(obj):
                return {f.name: serialize(getattr(obj, f.name)) for f in fields(obj)}
            if isinstance(obj, (list, tuple)):
                return [serialize(i) for i in obj]
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            return obj

        return dumps(serialize(settings)).encode("utf-8")

    @classmethod
    def convert(cls, data: bytes) -> "UserData":
        """Convert bytes back to UserSettings, rebuilding nested dataclasses and enums."""
        raw = loads(data.decode('utf-8'))

        return UserData(
            language=UserLanguage(raw["language"]),
            map_provider=MapProvider(raw["map_provider"]),
            user_type=UserType(raw["user_type"]),
            output_type=OutputType(raw["output_type"]),
            bot_state=InteractionStates(raw["bot_state"]),
            inline_buttons=BotMessage(**raw["inline_buttons"]),
            auto_alert=BotMessage(**raw["auto_alert"]),
            alert_set=raw["alert_set"],
            timer=TimedRecommendation(
                date_time=\
                    datetime.fromisoformat(raw["timer"]["date_time"])\
                    if raw["timer"]["date_time"] is not None\
                    else None,
                location=RoomNames.parse(raw["timer"]["location"])
            )
        )


class UserManager:
    DB_PATH = "settings.db"
    TABLE_NAME = "settings"

    _instance = None
    _refs = {}

    def __new__(cls, user: User | int | None = None):
        if cls._instance is None:
            aiosqlite.register_adapter(UserData, UserData.adapt)
            aiosqlite.register_converter("USERSETTINGS", UserData.convert)
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, user : User | int | None = None):
        """
        Opens database to access user information

        :param user: Telegram user to access
        """
        if isinstance(user, User):
            self._user = user.id
        elif isinstance(user, int):
            self._user = user
        else:
            self._user = None

    @property
    async def users(self) -> List[int]:
        """
        Retrieve all user IDs from the specified table in the SQLite database.

        Args:
            db_path (str): Path to the SQLite database file.
            table_name (str): Name of the table to query.

        Returns:
            list: A list of all user IDs in the table.
        """
        async with aiosqlite.connect(
            UserManager.DB_PATH,
            detect_types=PARSE_DECLTYPES
        ) as con:
            # Ensure table exists
            await con.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {UserManager.TABLE_NAME} (
                    user_id INTEGER PRIMARY KEY,
                    settings USERSETTINGS
                )
                """
            )

            # Fetch all users
            async with con.execute(
                f"""
                SELECT
                    user_id
                FROM {UserManager.TABLE_NAME}
                """
            ) as cursor:
                user_ids = [row[0] for row in await cursor.fetchall()]
                return user_ids

    async def _load_settings(self) -> UserData:
        if self._user is None:
            return UserData()

        async with aiosqlite.connect(
            UserManager.DB_PATH,
            detect_types=PARSE_DECLTYPES
        ) as con:
            # Ensure table exists
            await con.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {UserManager.TABLE_NAME} (
                    user_id INTEGER PRIMARY KEY,
                    settings USERSETTINGS
                )
                """
            )

            # Fetch data for user, or default data
            async with con.execute(
                f"""
                SELECT
                    settings
                FROM {UserManager.TABLE_NAME}
                WHERE user_id = ?
                """, (self._user,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result is not None else UserData()

    async def __aenter__(self) -> UserData:
        if self._user is None:
            return UserData()

        if self._user not in self._refs:
            self._refs[self._user] = await self._load_settings()

        return self._refs[self._user]

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool:
        if self._user is None:
            return False

        async with aiosqlite.connect(
            UserManager.DB_PATH,
            detect_types=PARSE_DECLTYPES
        ) as con:
            settings: UserData = self._refs[self._user]

            await con.execute(
                f"""
                INSERT OR REPLACE INTO {UserManager.TABLE_NAME} (
                    user_id,
                    settings
                ) VALUES (?, ?)
                """,
                (
                    self._user,
                    settings
                )
            )

            await con.commit()

        return True
