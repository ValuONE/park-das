from enum import Enum, auto
from json import dumps

from telebot.util import quick_markup
from telebot.types import Location, InlineKeyboardMarkup

class CarParkNames(Enum):
    P09 = "Parkplatz P09"
    P10 = "Parkplatz P10"
    P11 = "Parkplatz P11"
    P12 = "Parkplatz P12"
    P13 = "Parkplatz P13"
    P16 = "Parkplatz P16"
    P18 = "Parkplatz P18"
    P20 = "Parkhaus Mitte P20"
    P22 = "Parkplatz P22"
    P26 = "Parkplatz P26"
    P23 = "Parkplatz P23"
    P24 = "Parkplatz P24"
    P32 = "Parkplatz P32"
    P41 = "Parkplatz P41"
    P44 = "Parkplatz P44"
    M1 = "HNO Klinik M1"
    M2 = "Kliniken Michelsberg M2"
    M3 = "Frauenklinik M3"
    M4 = "Urologische Klinik M4"

    def get_pos(self) -> Location:
        return CAR_PARK_LOCATIONS[self]

    @classmethod
    def parse(cls, value):
        for member in CarParkNames:
            if member.value == value:
                return member
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
        CarParkNames.M1: Location(9.991174, 48.40938),
        CarParkNames.M2: Location(9.992269, 48.40819),
        CarParkNames.M3: Location(9.99374, 48.41076),
        CarParkNames.M4: Location(9.994923, 48.40974)
}

class SettingsEnum(Enum):
    @classmethod
    def markup_buttons(cls) -> InlineKeyboardMarkup:
        options = {str(opt) : {"callback_data" : dumps(
            {
                "k": cls.__name__,
                "v": opt.value
            }
        )} for opt in cls}
        options.pop("None")
        options["<< Zurück"] ={"callback_data" : "back"}
        return quick_markup(
            options,
            row_width=len(cls._member_names_) - 1
        )

class MapProvider(SettingsEnum):
    APPLE = auto()
    GOOGLE = auto()
    UNDEFINED = auto()

    def __str__(self) -> str:
        match(self):
            case MapProvider.APPLE:
                return "Apple 🍎"
            case MapProvider.GOOGLE:
                return "Google 🤖"
            case MapProvider.UNDEFINED:
                return "None"


class UserLanguage(SettingsEnum):
    EN = auto()
    DE = auto()
    UNDEFINED = auto()

    def __str__(self) -> str:
        match(self):
            case UserLanguage.DE:
                return "Deutsch 🇩🇪"
            case UserLanguage.EN:
                return "English 🇺🇸"
            case UserLanguage.UNDEFINED:
                return "None"


class UserType(SettingsEnum):
    VISITOR = auto()
    STUDENT = auto()
    UNDEFINED = auto()

    def __str__(self) -> str:
        match(self):
            case UserType.VISITOR:
                return "Besucher 🙋"
            case UserType.STUDENT:
                return "Mitarbeiter 🧑‍🔬"
            case UserType.UNDEFINED:
                return "None"
