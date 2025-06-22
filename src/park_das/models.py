from dataclasses import dataclass

import aiosqlite

from telebot.util import quick_markup
from telebot.types import Location, User, InlineKeyboardMarkup

import i18n

from .constants import CarParkNames, UserLanguage, UserType, MapProvider, InteractionStates

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

    _RATIO_FREE = 0.25
    _RATIO_CRITICAL = 0.1
    _RATIO_FULL = 0.0

    def get_pos(self) -> Location:
        """
        Returns the geographic position (latitude, longitude) of the car park.

        :return: A telegram location containing the latitude and longitude of the car park.
        """
        return self.name.get_pos()

    def almost_full(self) -> bool:
        """
        Determines if parking spot is basically full already

        :return: Flag whether spot is almost full
        """
        ratio = self.free_spaces / self.total_spaces
        return ratio < self._RATIO_CRITICAL

    def occupancy_level(self) -> str:
        """
        Get a visual representation of the current occupancy level

        :return: Emoji that signifies occupancy level
        """
        ratio = self.free_spaces / self.total_spaces
        if ratio > self._RATIO_FREE:
            return "✅"
        if self._RATIO_CRITICAL <= ratio < self._RATIO_FREE:
            return "⚠️"
        if self._RATIO_FULL < ratio < self._RATIO_CRITICAL:
            return "🛑"
        return "⛔️"

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

    # https://developers.google.com/maps/documentation/maps-static/start#Markers
    def to_map_marker(self, index : int) -> str:
        """
        Generates a formatted marker for the google maps api

        :param index: Index is used as label
        :return: Marker as formatted string
        """
        loc = self.get_pos()
        col = "gray"
        size = "tiny"

        ratio = self.free_spaces / self.total_spaces
        if ratio > self._RATIO_FREE:
            col = "green"
            size = ""
        if self._RATIO_CRITICAL <= ratio < self._RATIO_FREE:
            col = "yellow"
            size = "mid"
        if self._RATIO_FULL < ratio < self._RATIO_CRITICAL:
            col = "red"
            size = "small"
        return (
            f"color:{col}|"
            f"label:{index}|"
            f"size:{size}|"
            f"scale:2|"
            f"{loc.latitude},{loc.longitude}"
        )


@dataclass
class BotMessage:
    chat_id : int | None = None
    message_id : int | None = None

    @property
    def exists(self) -> bool:
        return self.chat_id is not None and self.message_id is not None


@dataclass
class RecommendationTimer:
    time: str | None = None
    date: str | None = None
    loc: str | None = None

    @property
    def exists(self) -> bool:
        return self.time is not None and self.date is not None

    @property
    def with_location(self) -> bool:
        return self.loc is not None

@dataclass
class UserSettings:
    language: UserLanguage = UserLanguage.UNDEFINED
    map_provider: MapProvider = MapProvider.UNDEFINED
    user_type: UserType = UserType.UNDEFINED
    bot_state: InteractionStates = InteractionStates.IDLE
    inline_buttons: BotMessage = BotMessage()
    auto_alert: BotMessage = BotMessage()
    alert_set: bool = False
    timer: RecommendationTimer = RecommendationTimer()

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
                    bot_state INTEGER NOT NULL,
                    inline_chat_id INTEGER,
                    inline_message_id INTEGER,
                    auto_alert_chat_id INTEGER,
                    auto_alert_message_id INTEGER,
                    alert_set INTEGER,
                    timer_time TEXT,
                    timer_date TEXT,
                    timer_loc TEXT
                )
                """
            )

            async with con.execute(
                """
                SELECT
                    language,
                    map_provider,
                    user_type,
                    bot_state,
                    inline_chat_id,
                    inline_message_id,
                    auto_alert_chat_id,
                    auto_alert_message_id,
                    alert_set,
                    timer_time,
                    timer_date,
                    timer_loc
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
                    bot_state=InteractionStates(result[3]),
                    inline_buttons=BotMessage(result[4], result[5]),
                    auto_alert=BotMessage(result[6], result[7]),
                    alert_set=bool(result[8]),
                    timer=RecommendationTimer(result[9], result[10], result[11])
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
            settings: UserSettings = self._refs[self._user.id]
            await con.execute(
                """
                INSERT OR REPLACE INTO settings (
                    user_id,
                    language,
                    map_provider,
                    user_type, bot_state,
                    inline_chat_id,
                    inline_message_id,
                    auto_alert_chat_id,
                    auto_alert_message_id,
                    alert_set,
                    timer_time,
                    timer_date,
                    timer_loc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self._user.id,
                    settings.language.value,
                    settings.map_provider.value,
                    settings.user_type.value,
                    settings.bot_state.value,
                    settings.inline_buttons.chat_id,
                    settings.inline_buttons.message_id,
                    settings.auto_alert.chat_id,
                    settings.auto_alert.message_id,
                    int(settings.alert_set),
                    settings.timer.time,
                    settings.timer.date,
                    settings.timer.loc
                )
            )
            await con.commit()

        return True
