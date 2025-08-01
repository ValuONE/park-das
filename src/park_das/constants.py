from enum import Enum, auto, IntEnum
from json import dumps

from telebot.util import quick_markup
from telebot.types import Location, InlineKeyboardMarkup

import i18n

class ParkingLotNames(Enum):
    """
    Describes all parking lots on campus and in the city
    """
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
    def parse(cls, value : str):
        for member in ParkingLotNames:
            if member.value == value:
                return member
            if value == "Parkhaus Mitte P20":
                return cls.P20
        raise KeyError(f"No matching enum member for '{value}' found.")

class RoomNames(Enum):
    """
    Describes all rooms, lecture halls, .. on campus and in the city
    """
    UNDEFINED = "rooms.undefined"
    UNI_WEST = "rooms.uni_west"
    UNI_OST = "rooms.uni_ost"
    HELMHOLTZSTRASSE = "rooms.helmholtzstrasse"
    KLINIKEN_MICHELSBERG = "rooms.kliniken_michelsberg"
    O25_H1 = "rooms.o25_h1"
    O25_H2 = "rooms.o25_h2"
    N25_H3 = "rooms.n25_h3"
    O25_H4_5 = "rooms.o25_h4_5"
    O25_H7 = "rooms.o25_h7"
    N25_H8 = "rooms.n25_h8"
    N25_H9 = "rooms.n25_h9"
    M24_H10 = "rooms.m24_h10"
    N24_H11 = "rooms.n24_h11"
    N24_H12 = "rooms.n24_h12"
    N24_H13 = "rooms.n24_h13"
    N24_H14 = "rooms.n24_h14"
    N24_H15 = "rooms.n24_h15"
    N24_H16 = "rooms.n24_h16"
    O27_H20 = "rooms.o27_h20"
    O28_H21 = "rooms.o28_h21"
    O28_H22 = "rooms.o28_h22"
    M28_H2101_TTU = "rooms.m28_h2101_ttu"
    H218_MIKROSKOPIERSAAL = "rooms.h218_mikroskopiersaal"
    H45_1_BLAUER_HOERSAAL = "rooms.h45_1_blauer_hoersaal"
    H45_2_GELBER_HOERSAAL = "rooms.h45_2_gelber_hoersaal"
    H47_0_501_ROTER_HOERSAAL = "rooms.h47_0_501_roter_hoersaal"
    HOERSAAL_CHIRURGIE = "rooms.hoersaal_chirurgie"
    HOERSAAL_INNERE_MEDIZIN = "rooms.hoersaal_innere_medizin"
    N23_SEMINARRAUM_2622 = "rooms.n23_seminarraum_2622"
    N24_SEMINARRAUM_104 = "rooms.n24_seminarraum_104"
    N24_SEMINARRAUM_131 = "rooms.n24_seminarraum_131"
    N24_SEMINARRAUM_155 = "rooms.n24_seminarraum_155"
    N24_SEMINARRAUM_226 = "rooms.n24_seminarraum_226"
    N24_SEMINARRAUM_227 = "rooms.n24_seminarraum_227"
    N24_SEMINARRAUM_251 = "rooms.n24_seminarraum_251"
    N24_SEMINARRAUM_252 = "rooms.n24_seminarraum_252"
    N24_SEMINARRAUM_254 = "rooms.n24_seminarraum_254"
    N25_SEMINARRAUM_2101 = "rooms.n25_seminarraum_2101"
    N25_SEMINARRAUM_2102 = "rooms.n25_seminarraum_2102"
    N25_SEMINARRAUM_2103 = "rooms.n25_seminarraum_2103"
    O23_SEMINARRAUM_2609_10 = "rooms.o23_seminarraum_2609_10"
    O23_SEMINARRAUM_2611 = "rooms.o23_seminarraum_2611"
    O25_SEMINARRAUM_151 = "rooms.o25_seminarraum_151"
    O25_SEMINARRAUM_169 = "rooms.o25_seminarraum_169"
    O25_SEMINARRAUM_346 = "rooms.o25_seminarraum_346"
    O27_SEMINARRAUM_121 = "rooms.o27_seminarraum_121"
    O27_SEMINARRAUM_122 = "rooms.o27_seminarraum_122"
    O27_SEMINARRAUM_123 = "rooms.o27_seminarraum_123"
    O27_SEMINARRAUM_2201 = "rooms.o27_seminarraum_2201"
    O27_SEMINARRAUM_2202 = "rooms.o27_seminarraum_2202"
    O27_SEMINARRAUM_2203 = "rooms.o27_seminarraum_2203"
    O28_SEMINARRAUM_2001 = "rooms.o28_seminarraum_2001"
    O28_SEMINARRAUM_2002 = "rooms.o28_seminarraum_2002"
    O28_SEMINARRAUM_2003 = "rooms.o28_seminarraum_2003"
    O28_SEMINARRAUM_2004 = "rooms.o28_seminarraum_2004"
    O29_SEMINARRAUM_1001 = "rooms.o29_seminarraum_1001"
    O29_SEMINARRAUM_1002 = "rooms.o29_seminarraum_1002"
    O29_SEMINARRAUM_1003 = "rooms.o29_seminarraum_1003"
    O29_SEMINARRAUM_2001 = "rooms.o29_seminarraum_2001"
    O29_SEMINARRAUM_2002 = "rooms.o29_seminarraum_2002"
    O29_SEMINARRAUM_2003 = "rooms.o29_seminarraum_2003"
    O29_SEMINARRAUM_2004 = "rooms.o29_seminarraum_2004"
    O29_SEMINARRAUM_2005 = "rooms.o29_seminarraum_2005"
    O29_SEMINARRAUM_2006 = "rooms.o29_seminarraum_2006"
    O29_SEMINARRAUM_3001 = "rooms.o29_seminarraum_3001"
    O29_SEMINARRAUM_3002 = "rooms.o29_seminarraum_3002"
    O29_SEMINARRAUM_3003 = "rooms.o29_seminarraum_3003"
    O29_SEMINARRAUM_3004 = "rooms.o29_seminarraum_3004"
    SRGEB_RAUM_2_AEA_12 = "rooms.srgeb_raum_2_aea_12"
    SEMINARRAUM_43_2_101 = "rooms.seminarraum_43_2_101"
    SEMINARRAUM_43_2_102 = "rooms.seminarraum_43_2_102"
    SEMINARRAUM_43_2_103 = "rooms.seminarraum_43_2_103"
    SEMINARRAUM_43_2_104 = "rooms.seminarraum_43_2_104"
    SEMINARRAUM_45_2_101 = "rooms.seminarraum_45_2_101"
    SEMINARRAUM_45_2_102 = "rooms.seminarraum_45_2_102"
    SEMINARRAUM_45_2_103 = "rooms.seminarraum_45_2_103"
    SEMINARRAUM_47_2_101 = "rooms.seminarraum_47_2_101"
    SEMINARRAUM_47_2_102 = "rooms.seminarraum_47_2_102"
    SEMINARRAUM_47_2_104 = "rooms.seminarraum_47_2_104"
    SEMINARRAUM_47_1_504 = "rooms.seminarraum_47_1_504"
    SEMINARRAUM_47_1_506 = "rooms.seminarraum_47_1_506"
    SEMINARRAUM_47_1_507 = "rooms.seminarraum_47_1_507"
    SEMINARRAUM_47_1_508 = "rooms.seminarraum_47_1_508"
    SEMINARRAUM_47_2_503 = "rooms.seminarraum_47_2_503"
    SEMINARRAUM_47_2_505 = "rooms.seminarraum_47_2_505"
    SEMINARRAUM_47_2_506 = "rooms.seminarraum_47_2_506"
    SEMINARRAUM_47_2_507 = "rooms.seminarraum_47_2_507"
    HH_18_HOERSAAL_120 = "rooms.hh_18_hoersaal_120"
    HH_18_HOERSAAL_220 = "rooms.hh_18_hoersaal_220"
    HH_18_HOERSAAL_E20 = "rooms.hh_18_hoersaal_e20"
    HH_18_HOERSAAL_E60 = "rooms.hh_18_hoersaal_e60"
    HH_22_PRAKTIKUMSRAUM_1_41 = "rooms.hh_22_praktikumsraum_1_41"
    HH_22_SEMINARRAUM_1_42 = "rooms.hh_22_seminarraum_1_42"
    HH_22_SEMINARRAUM_E_03 = "rooms.hh_22_seminarraum_e_03"
    HH_22_SEMINARRAUM_E_04 = "rooms.hh_22_seminarraum_e_04"
    HOERSAAL_E30 = "rooms.hoersaal_e30"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        """
        Get valid i18n key

        :return: i18n key
        """
        return self.value

    @classmethod
    def parse(cls, value : str):
        for member in cls:
            if member.value == value:
                return member
        raise KeyError(f"No matching enum member for '{value}' found.")

PARKING_LOT_LOCATIONS = {
    ParkingLotNames.P09: Location(9.942359, 48.41912),
    ParkingLotNames.P10: Location(9.943917, 48.42005),
    ParkingLotNames.P11: Location(9.944910, 48.42046),
    ParkingLotNames.P12: Location(9.945848, 48.42076),
    ParkingLotNames.P13: Location(9.945848, 48.42076),
    ParkingLotNames.P16: Location(9.947908, 48.42263),
    ParkingLotNames.P18: Location(9.949502, 48.42304),
    ParkingLotNames.P20: Location(9.951033, 48.42396),
    ParkingLotNames.P22: Location(9.954085, 48.42506),
    ParkingLotNames.P26: Location(9.951642, 48.42389),
    ParkingLotNames.P23: Location(9.954960, 48.42543),
    ParkingLotNames.P24: Location(9.953938, 48.42481),
    ParkingLotNames.P32: Location(9.957266, 48.42410),
    ParkingLotNames.P41: Location(9.958382, 48.42599),
    ParkingLotNames.P44: Location(9.962580, 48.42602),
    ParkingLotNames.HE: Location(9.958027, 48.42585),
    ParkingLotNames.M1: Location(9.991174, 48.40938),
    ParkingLotNames.M2: Location(9.992269, 48.40819),
    ParkingLotNames.M3: Location(9.99374, 48.41076),
    ParkingLotNames.M4: Location(9.994923, 48.40974)
}

ROOM_LOCATIONS = {
    RoomNames.UNI_OST: Location(9.955421, 48.422561),
    RoomNames.UNI_WEST: Location(9.946281, 48.420272),
    RoomNames.HELMHOLTZSTRASSE: Location(9.963221, 48.425570),
    RoomNames.KLINIKEN_MICHELSBERG: Location(9.992790, 48.409970),
    RoomNames.O25_H1: Location(9.95584, 48.4225),
    RoomNames.O25_H2: Location(9.95565, 48.4226),
    RoomNames.N25_H3: Location(9.95568, 48.42278),
    RoomNames.O25_H4_5: Location(9.9552, 48.4225),
    RoomNames.O25_H7: Location(9.95604, 48.42237),
    RoomNames.N25_H8: Location(9.9552, 48.42297),
    RoomNames.N25_H9: Location(9.95509, 48.4231),
    RoomNames.M24_H10: Location(9.95377, 48.42331),
    RoomNames.N24_H11: Location(9.95431, 48.42229),
    RoomNames.N24_H12: Location(9.95407, 48.42259),
    RoomNames.N24_H13: Location(9.95388, 48.42258),
    RoomNames.N24_H14: Location(9.95431, 48.42229),
    RoomNames.N24_H15: Location(9.95407, 48.42259),
    RoomNames.N24_H16: Location(9.95388, 48.42258),
    RoomNames.O27_H20: Location(9.9575, 48.42277),
    RoomNames.O28_H21: Location(9.95778, 48.423),
    RoomNames.O28_H22: Location(9.95801, 48.42306),
    RoomNames.M28_H2101_TTU: Location(9.95662, 48.42437),
    RoomNames.H218_MIKROSKOPIERSAAL: Location(9.95627, 48.42324),
    RoomNames.H45_1_BLAUER_HOERSAAL: Location(9.94676, 48.41949),
    RoomNames.H45_2_GELBER_HOERSAAL: Location(9.94632, 48.41974),
    RoomNames.H47_0_501_ROTER_HOERSAAL: Location(9.94443, 48.42011),
    RoomNames.HOERSAAL_CHIRURGIE: Location(9.95301, 48.42243),
    RoomNames.HOERSAAL_INNERE_MEDIZIN: Location(9.95365, 48.42185),
    RoomNames.N23_SEMINARRAUM_2622: Location(9.95383, 48.42216),
    RoomNames.N24_SEMINARRAUM_104: Location(9.95436, 48.42264),
    RoomNames.N24_SEMINARRAUM_131: Location(9.95473, 48.42259),
    RoomNames.N24_SEMINARRAUM_155: Location(9.95431, 48.4224),
    RoomNames.N24_SEMINARRAUM_226: Location(9.95461, 48.42271),
    RoomNames.N24_SEMINARRAUM_227: Location(9.95461, 48.42271),
    RoomNames.N24_SEMINARRAUM_251: Location(9.95465, 48.42236),
    RoomNames.N24_SEMINARRAUM_252: Location(9.95465, 48.42236),
    RoomNames.N24_SEMINARRAUM_254: Location(9.95432, 48.42241),
    RoomNames.N25_SEMINARRAUM_2101: Location(9.95486, 48.42303),
    RoomNames.N25_SEMINARRAUM_2102: Location(9.95491, 48.42296),
    RoomNames.N25_SEMINARRAUM_2103: Location(9.95496, 48.42289),
    RoomNames.O23_SEMINARRAUM_2609_10: Location(9.95398, 48.42195),
    RoomNames.O23_SEMINARRAUM_2611: Location(9.95406, 48.42187),
    RoomNames.O25_SEMINARRAUM_151: Location(9.95537, 48.42205),
    RoomNames.O25_SEMINARRAUM_169: Location(9.95578, 48.42228),
    RoomNames.O25_SEMINARRAUM_346: Location(9.95518, 48.42258),
    RoomNames.O27_SEMINARRAUM_121: Location(9.95755, 48.42306),
    RoomNames.O27_SEMINARRAUM_122: Location(9.95755, 48.42305),
    RoomNames.O27_SEMINARRAUM_123: Location(9.95764, 48.42296),
    RoomNames.O27_SEMINARRAUM_2201: Location(9.95745, 48.42301),
    RoomNames.O27_SEMINARRAUM_2202: Location(9.95755, 48.42305),
    RoomNames.O27_SEMINARRAUM_2203: Location(9.95761, 48.42295),
    RoomNames.O28_SEMINARRAUM_2001: Location(9.95779, 48.42311),
    RoomNames.O28_SEMINARRAUM_2002: Location(9.95779, 48.42311),
    RoomNames.O28_SEMINARRAUM_2003: Location(9.95792, 48.42316),
    RoomNames.O28_SEMINARRAUM_2004: Location(9.95792, 48.42316),
    RoomNames.O29_SEMINARRAUM_1001: Location(9.95778, 48.42329),
    RoomNames.O29_SEMINARRAUM_1002: Location(9.95778, 48.42329),
    RoomNames.O29_SEMINARRAUM_1003: Location(9.95778, 48.42329),
    RoomNames.O29_SEMINARRAUM_2001: Location(9.95778, 48.42329),
    RoomNames.O29_SEMINARRAUM_2002: Location(9.95778, 48.42329),
    RoomNames.O29_SEMINARRAUM_2003: Location(9.95778, 48.42329),
    RoomNames.O29_SEMINARRAUM_2004: Location(9.95778, 48.42329),
    RoomNames.O29_SEMINARRAUM_2005: Location(9.95778, 48.42329),
    RoomNames.O29_SEMINARRAUM_2006: Location(9.95778, 48.42329),
    RoomNames.O29_SEMINARRAUM_3001: Location(9.95778, 48.42329),
    RoomNames.O29_SEMINARRAUM_3002: Location(9.95778, 48.42329),
    RoomNames.O29_SEMINARRAUM_3003: Location(9.95778, 48.42329),
    RoomNames.O29_SEMINARRAUM_3004: Location(9.95778, 48.42329),
    RoomNames.SRGEB_RAUM_2_AEA_12: Location(9.95253, 48.42472),
    RoomNames.SEMINARRAUM_43_2_101: Location(9.94715, 48.42019),
    RoomNames.SEMINARRAUM_43_2_102: Location(9.94706, 48.42012),
    RoomNames.SEMINARRAUM_43_2_103: Location(9.94696, 48.42004),
    RoomNames.SEMINARRAUM_43_2_104: Location(9.94683, 48.41994),
    RoomNames.SEMINARRAUM_45_2_101: Location(9.94633, 48.4196),
    RoomNames.SEMINARRAUM_45_2_102: Location(9.94625, 48.41954),
    RoomNames.SEMINARRAUM_45_2_103: Location(9.94611, 48.41944),
    RoomNames.SEMINARRAUM_47_2_101: Location(9.94544, 48.41896),
    RoomNames.SEMINARRAUM_47_2_102: Location(9.94559, 48.41906),
    RoomNames.SEMINARRAUM_47_2_104: Location(9.94574, 48.41918),
    RoomNames.SEMINARRAUM_47_1_504: Location(9.94446, 48.42002),
    RoomNames.SEMINARRAUM_47_1_506: Location(9.94448, 48.42014),
    RoomNames.SEMINARRAUM_47_1_507: Location(9.94453, 48.42007),
    RoomNames.SEMINARRAUM_47_1_508: Location(9.94458, 48.42002),
    RoomNames.SEMINARRAUM_47_2_503: Location(9.94446, 48.42002),
    RoomNames.SEMINARRAUM_47_2_505: Location(9.94448, 48.42014),
    RoomNames.SEMINARRAUM_47_2_506: Location(9.94453, 48.42007),
    RoomNames.SEMINARRAUM_47_2_507: Location(9.94458, 48.42002),
    RoomNames.HH_18_HOERSAAL_120: Location(9.96351, 48.42532),
    RoomNames.HH_18_HOERSAAL_220: Location(9.96351, 48.42532),
    RoomNames.HH_18_HOERSAAL_E20: Location(9.96351, 48.42532),
    RoomNames.HH_18_HOERSAAL_E60: Location(9.96351, 48.42532),
    RoomNames.HH_22_PRAKTIKUMSRAUM_1_41: Location(9.96308, 48.42582),
    RoomNames.HH_22_SEMINARRAUM_1_42: Location(9.96308, 48.42582),
    RoomNames.HH_22_SEMINARRAUM_E_03: Location(9.96308, 48.42582),
    RoomNames.HH_22_SEMINARRAUM_E_04: Location(9.96308, 48.42582),
    RoomNames.HOERSAAL_E30: Location(9.99279, 48.40997)
}

class SettingsEnum(Enum):
    """
    Parent class for all user changeable settings
    """

    @classmethod
    def markup_buttons(cls, lang : str) -> InlineKeyboardMarkup:
        """
        Creates inline buttons based on the available settings

        :return: A set of inline buttons to attach to a message
        """
        options = {i18n.t(repr(opt), lang): {"callback_data": dumps(
            {
                "type": Callbacks.SETTINGS_UPDATE,
                cls.__name__: opt.value
            }
        )} for opt in cls if repr(opt) != "settings.undefined"}
        options[i18n.t("settings.back", lang)] = {
            "callback_data" : dumps({"type":Callbacks.SETTINGS_BACK})
        }
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
    """
    Describes available map providers for navigation
    """
    APPLE = "settings.mapprovider.apple"
    GOOGLE = "settings.mapprovider.google"
    UNDEFINED = "settings.undefined"

class UserLanguage(SettingsEnum):
    """
    Describes available output languages
    """
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
    """
    Describes kinds of people using the bot
    """
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
    """
    Describes available output types
    """
    TEXT = "settings.outputtype.text"
    VOICE = "settings.outputtype.voice"
    UNDEFINED = "settings.undefined"

class Settings(Enum):
    """
    Describes settings / preferences that a user can change
    """
    MAPPROVIDER = MapProvider
    USERLANGUAGE = UserLanguage
    USERTYPE = UserType
    OUTPUTTYPE = OutputType

    @classmethod
    def parse(cls, name):
        for member in cls:
            if member.name == name:
                return member
        raise KeyError(f"No matching enum member for '{name}' found.")

class InteractionStates(IntEnum):
    """
    Describes conversation states a user can be in
    """
    IDLE = auto()
    NEED_DATE_TIME = auto()
    PROXIMITY_TRIGGERED = auto()

class Callbacks(IntEnum):
    """
    Describes intent of callbacks from a user
    """
    SETTINGS_BACK = auto()
    SETTINGS_UPDATE = auto()
    SETTINGS_SELECT = auto()
    MAP_PROVIDER_ERROR = auto()
    UNDEFINED = auto()

class BotCommands(Enum):
    """
    Describes commands available to the user
    """
    NAVIGATION = "Navigation"
    TIMER = "Timing"
    AUTOMATIC = "Automatic"
    RECOMMEND = "Recommend"
    OVERVIEW = "Overview"
    UNKNOWN = "Unknown"

    @classmethod
    def parse(cls, to_parse : str | None):
        if to_parse is None:
            return BotCommands.UNKNOWN
        for com in BotCommands:
            if to_parse.find(com.value) != -1:
                return com
        return BotCommands.UNKNOWN
