from enum import Enum, auto
from json import dumps

from telebot.util import quick_markup
from telebot.types import Location, InlineKeyboardMarkup

import i18n

class CarParkNames(Enum):
    P09 = "Parkplatz P09"
    P10 = "Parkplatz P10"
    P11 = "Parkplatz P11"
    P12 = "Parkplatz P12"
    P13 = "Parkplatz P13"
    P16 = "Parkplatz P16"
    P18 = "Parkplatz P18"
    P20 = "PH Mitte P20"
    P22 = "Parkplatz P22"
    P26 = "Parkplatz P26"
    P23 = "Parkplatz P23"
    P24 = "Parkplatz P24"
    P32 = "Parkplatz P32"
    P41 = "Parkplatz P41"
    P44 = "Parkplatz P44"
    HE = "PH Helmholtzstr."
    M1 = "HNO Klinik M1"
    M2 = "Kliniken Michelsberg M2"
    M3 = "Frauenklinik M3"
    M4 = "Urologische Klinik M4"

    def __str__(self) -> str:
        return self.name

    @classmethod
    def parse(cls, value):
        for member in CarParkNames:
            if member.value == value:
                return member
            if value == "Parkhaus Mitte P20":
                return cls.P20
        raise KeyError(f"No matching enum member for '{value}' found.")

CAR_PARK_LOCATIONS = {
    CarParkNames.P09: Location(9.942359, 48.41912),
    CarParkNames.P10: Location(9.943917, 48.42005),
    CarParkNames.P11: Location(9.944910, 48.42046),
    CarParkNames.P12: Location(9.945848, 48.42076),
    CarParkNames.P13: Location(9.945848, 48.42076),
    CarParkNames.P16: Location(9.947908, 48.42263),
    CarParkNames.P18: Location(9.949502, 48.42304),
    CarParkNames.P20: Location(9.951033, 48.42396),
    CarParkNames.P22: Location(9.954085, 48.42506),
    CarParkNames.P26: Location(9.951642, 48.42389),
    CarParkNames.P23: Location(9.954960, 48.42543),
    CarParkNames.P24: Location(9.953938, 48.42481),
    CarParkNames.P32: Location(9.957266, 48.42410),
    CarParkNames.P41: Location(9.958382, 48.42599),
    CarParkNames.P44: Location(9.962580, 48.42602),
    CarParkNames.HE: Location(9.958027, 48.42585),
    CarParkNames.M1: Location(9.991174, 48.40938),
    CarParkNames.M2: Location(9.992269, 48.40819),
    CarParkNames.M3: Location(9.99374, 48.41076),
    CarParkNames.M4: Location(9.994923, 48.40974)
}

class SettingsEnum(Enum):
    @classmethod
    def markup_buttons(cls, lang : str) -> InlineKeyboardMarkup:
        """
        Creates inline buttons based on the available settings

        :return: A set of inline buttons to attach to a message
        """
        options = {i18n.t(repr(opt), lang): {"callback_data": dumps(
            {
                cls.__name__: opt.value
            }
        )} for opt in cls if repr(opt) != "settings.undefined"}
        options[i18n.t("settings.back", lang)] = {"callback_data": "back"}
        return quick_markup(
            options,
            row_width=1
        )

    def __repr__(self) -> str:
        """
        Get valid i18n key

        :return: i18n key
        """
        return self.value

class MapProvider(SettingsEnum):
    APPLE = "settings.mapprovider.apple"
    GOOGLE = "settings.mapprovider.google"
    UNDEFINED = "settings.undefined"

class UserLanguage(SettingsEnum):
    EN = "settings.language.en"
    DE = "settings.language.de"
    UNDEFINED = "settings.undefined"

    def __str__(self) -> str:
        """
        Get enum value as language code

        :return: Language code string
        """
        return self.name.lower()

class UserType(SettingsEnum):
    VISITOR = "settings.usertype.visitor"
    WORKER = "settings.usertype.student"
    CITY = "settings.usertype.city"
    UNDEFINED = "settings.undefined"

    @property
    def live_pos(self) -> Location:
        """
        Get an appropriately centered location with proximity alert for user type

        :return: Centered location with proximity radius set
        """
        match self:
            case UserType.CITY:
                return Location(
                    9.99268,
                    48.40973,
                    proximity_alert_radius=500,
                    live_period=0x7FFFFFFF
                )
            case _:
                return Location(
                    9.94540,
                    48.42341,
                    proximity_alert_radius=1000,
                    live_period=0x7FFFFFFF
                )

class OutputType(SettingsEnum):
    TEXT = "settings.outputtype.text"
    VOICE = "settings.outputtype.voice"
    UNDEFINED = "settings.undefined"

class InteractionStates(Enum):
    IDLE = auto()
    NEED_DATE_TIME = auto()
    PROXIMITY_TRIGGERED = auto()
