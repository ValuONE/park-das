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

class RoomNames(Enum):
    O25_H1 = "O25 H1"
    O25_H2 = "O25 H2"
    N25_H3 = "N25 H3"
    O25_H4_5 = "O25 H4/5"
    O25_H7 = "O25 H7"
    N25_H8 = "N25 H8"
    N25_H9 = "N25 H9"
    M24_H10 = "M24 H10"
    N24_H11 = "N24 H11"
    N24_H12 = "N24 H12"
    N24_H13 = "N24 H13"
    N24_H14 = "N24 H14"
    N24_H15 = "N24 H15"
    N24_H16 = "N24 H16"
    O27_H20 = "O27 H20"
    O28_H21 = "O28 H21"
    O28_H22 = "O28 H22"
    M28_H2101_TTU = "M28 H2101 (TTU)"
    H218_Mikroskopiersaal = "H218 - Mikroskopiersaal"
    H45_1_Blauer_Hörsaal = "H45.1 - Blauer Hörsaal"
    H45_2_Gelber_Hörsaal = "H45.2 - Gelber Hörsaal"
    H47_0_501_Roter_Hörsaal = "H47.0.501 - Roter Hörsaal"
    Hörsaal_Chirurgie = "Hörsaal Chirurgie"
    Hörsaal_Innere_Medizin = "Hörsaal Innere Medizin"
    N23_Seminarraum_2622 = "N23 Seminarraum 2622"
    N24_Seminarraum_104 = "N24 Seminarraum 104"
    N24_Seminarraum_131 = "N24 Seminarraum 131"
    N24_Seminarraum_155 = "N24 Seminarraum 155"
    N24_Seminarraum_226 = "N24 Seminarraum 226"
    N24_Seminarraum_227 = "N24 Seminarraum 227"
    N24_Seminarraum_251 = "N24 Seminarraum 251"
    N24_Seminarraum_252 = "N24 Seminarraum 252"
    N24_Seminarraum_254 = "N24 Seminarraum 254"
    N25_Seminarraum_2101 = "N25 Seminarraum 2101"
    N25_Seminarraum_2102 = "N25 Seminarraum 2102"
    N25_Seminarraum_2103 = "N25 Seminarraum 2103"
    O23_Seminarraum_2609_10 = "O23 Seminarraum 2609/10"
    O23_Seminarraum_2611 = "O23 Seminarraum 2611"
    O25_Seminarraum_151 = "O25 Seminarraum 151"
    O25_Seminarraum_169 = "O25 Seminarraum 169"
    O25_Seminarraum_346 = "O25 Seminarraum 346"
    O27_Seminarraum_121 = "O27 Seminarraum 121"
    O27_Seminarraum_122 = "O27 Seminarraum 122"
    O27_Seminarraum_123 = "O27 Seminarraum 123"
    O27_Seminarraum_2201 = "O27 Seminarraum 2201"
    O27_Seminarraum_2202 = "O27 Seminarraum 2202"
    O27_Seminarraum_2203 = "O27 Seminarraum 2203"
    O28_Seminarraum_2001 = "O28 Seminarraum 2001"
    O28_Seminarraum_2002 = "O28 Seminarraum 2002"
    O28_Seminarraum_2003 = "O28 Seminarraum 2003"
    O28_Seminarraum_2004 = "O28 Seminarraum 2004"
    O29_Seminarraum_1001 = "O29 Seminarraum 1001"
    O29_Seminarraum_1002 = "O29 Seminarraum 1002"
    O29_Seminarraum_1003 = "O29 Seminarraum 1003"
    O29_Seminarraum_2001 = "O29 Seminarraum 2001"
    O29_Seminarraum_2002 = "O29 Seminarraum 2002"
    O29_Seminarraum_2003 = "O29 Seminarraum 2003"
    O29_Seminarraum_2004 = "O29 Seminarraum 2004"
    O29_Seminarraum_2005 = "O29 Seminarraum 2005"
    O29_Seminarraum_2006 = "O29 Seminarraum 2006"
    O29_Seminarraum_3001 = "O29 Seminarraum 3001"
    O29_Seminarraum_3002 = "O29 Seminarraum 3002"
    O29_Seminarraum_3003 = "O29 Seminarraum 3003"
    O29_Seminarraum_3004 = "O29 Seminarraum 3004"
    SRgeb_Raum_2_AEA_12 = "SRgeb Raum 2, AEA 12"
    Seminarraum_43_2_101 = "Seminarraum 43.2.101"
    Seminarraum_43_2_102 = "Seminarraum 43.2.102"
    Seminarraum_43_2_103 = "Seminarraum 43.2.103"
    Seminarraum_43_2_104 = "Seminarraum 43.2.104"
    Seminarraum_45_2_101 = "Seminarraum 45.2.101"
    Seminarraum_45_2_102 = "Seminarraum 45.2.102"
    Seminarraum_45_2_103 = "Seminarraum 45.2.103"
    Seminarraum_47_2_101 = "Seminarraum 47.2.101"
    Seminarraum_47_2_102 = "Seminarraum 47.2.102"
    Seminarraum_47_2_104 = "Seminarraum 47.2.104"
    Seminarraum_47_1_504 = "Seminarraum 47.1.504"
    Seminarraum_47_1_506 = "Seminarraum 47.1.506"
    Seminarraum_47_1_507 = "Seminarraum 47.1.507"
    Seminarraum_47_1_508 = "Seminarraum 47.1.508"
    Seminarraum_47_2_503 = "Seminarraum 47.2.503"
    Seminarraum_47_2_505 = "Seminarraum 47.2.505"
    Seminarraum_47_2_506 = "Seminarraum 47.2.506"
    Seminarraum_47_2_507 = "Seminarraum 47.2.507"
    HH_18_Hörsaal_120 = "HH 18 - Hörsaal 120"
    HH_18_Hörsaal_220 = "HH 18 - Hörsaal 220"
    HH_18_Hörsaal_E20 = "HH 18 - Hörsaal E20"
    HH_18_Hörsaal_E60 = "HH 18 - Hörsaal E60"
    HH_22_Praktikumsraum_1_41 = "HH 22 - Praktikumsraum 1.41"
    HH_22_Seminarraum_1_42 = "HH 22 - Seminarraum 1.42"
    HH_22_Seminarraum_E_03 = "HH 22 - Seminarraum E.03"
    HH_22_Seminarraum_E_04 = "HH 22 - Seminarraum E.04"
    Hörsaal_E30 = "Hörsaal - E30"

    def __str__(self) -> str:
        return self.name

    @classmethod
    def parse(cls, value):
        for member in cls:
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
    CarParkNames.HE: Location(9.958027, 48.42585),
    CarParkNames.M1: Location(9.991174, 48.40938),
    CarParkNames.M2: Location(9.992269, 48.40819),
    CarParkNames.M3: Location(9.99374, 48.41076),
    CarParkNames.M4: Location(9.994923, 48.40974)
}

ROOM_LOCATIONS = {
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
    RoomNames.H218_Mikroskopiersaal: Location(9.95627, 48.42324),
    RoomNames.H45_1_Blauer_Hörsaal: Location(9.94676, 48.41949),
    RoomNames.H45_2_Gelber_Hörsaal: Location(9.94632, 48.41974),
    RoomNames.H47_0_501_Roter_Hörsaal: Location(9.94443, 48.42011),
    RoomNames.Hörsaal_Chirurgie: Location(9.95301, 48.42243),
    RoomNames.Hörsaal_Innere_Medizin: Location(9.95365, 48.42185),
    RoomNames.N23_Seminarraum_2622: Location(9.95383, 48.42216),
    RoomNames.N24_Seminarraum_104: Location(9.95436, 48.42264),
    RoomNames.N24_Seminarraum_131: Location(9.95473, 48.42259),
    RoomNames.N24_Seminarraum_155: Location(9.95431, 48.4224),
    RoomNames.N24_Seminarraum_226: Location(9.95461, 48.42271),
    RoomNames.N24_Seminarraum_227: Location(9.95461, 48.42271),
    RoomNames.N24_Seminarraum_251: Location(9.95465, 48.42236),
    RoomNames.N24_Seminarraum_252: Location(9.95465, 48.42236),
    RoomNames.N24_Seminarraum_254: Location(9.95432, 48.42241),
    RoomNames.N25_Seminarraum_2101: Location(9.95486, 48.42303),
    RoomNames.N25_Seminarraum_2102: Location(9.95491, 48.42296),
    RoomNames.N25_Seminarraum_2103: Location(9.95496, 48.42289),
    RoomNames.O23_Seminarraum_2609_10: Location(9.95398, 48.42195),
    RoomNames.O23_Seminarraum_2611: Location(9.95406, 48.42187),
    RoomNames.O25_Seminarraum_151: Location(9.95537, 48.42205),
    RoomNames.O25_Seminarraum_169: Location(9.95578, 48.42228),
    RoomNames.O25_Seminarraum_346: Location(9.95518, 48.42258),
    RoomNames.O27_Seminarraum_121: Location(9.95755, 48.42306),
    RoomNames.O27_Seminarraum_122: Location(9.95755, 48.42305),
    RoomNames.O27_Seminarraum_123: Location(9.95764, 48.42296),
    RoomNames.O27_Seminarraum_2201: Location(9.95745, 48.42301),
    RoomNames.O27_Seminarraum_2202: Location(9.95755, 48.42305),
    RoomNames.O27_Seminarraum_2203: Location(9.95761, 48.42295),
    RoomNames.O28_Seminarraum_2001: Location(9.95779, 48.42311),
    RoomNames.O28_Seminarraum_2002: Location(9.95779, 48.42311),
    RoomNames.O28_Seminarraum_2003: Location(9.95792, 48.42316),
    RoomNames.O28_Seminarraum_2004: Location(9.95792, 48.42316),
    RoomNames.O29_Seminarraum_1001: Location(9.95778, 48.42329),
    RoomNames.O29_Seminarraum_1002: Location(9.95778, 48.42329),
    RoomNames.O29_Seminarraum_1003: Location(9.95778, 48.42329),
    RoomNames.O29_Seminarraum_2001: Location(9.95778, 48.42329),
    RoomNames.O29_Seminarraum_2002: Location(9.95778, 48.42329),
    RoomNames.O29_Seminarraum_2003: Location(9.95778, 48.42329),
    RoomNames.O29_Seminarraum_2004: Location(9.95778, 48.42329),
    RoomNames.O29_Seminarraum_2005: Location(9.95778, 48.42329),
    RoomNames.O29_Seminarraum_2006: Location(9.95778, 48.42329),
    RoomNames.O29_Seminarraum_3001: Location(9.95778, 48.42329),
    RoomNames.O29_Seminarraum_3002: Location(9.95778, 48.42329),
    RoomNames.O29_Seminarraum_3003: Location(9.95778, 48.42329),
    RoomNames.O29_Seminarraum_3004: Location(9.95778, 48.42329),
    RoomNames.SRgeb_Raum_2_AEA_12: Location(9.95253, 48.42472),
    RoomNames.Seminarraum_43_2_101: Location(9.94715, 48.42019),
    RoomNames.Seminarraum_43_2_102: Location(9.94706, 48.42012),
    RoomNames.Seminarraum_43_2_103: Location(9.94696, 48.42004),
    RoomNames.Seminarraum_43_2_104: Location(9.94683, 48.41994),
    RoomNames.Seminarraum_45_2_101: Location(9.94633, 48.4196),
    RoomNames.Seminarraum_45_2_102: Location(9.94625, 48.41954),
    RoomNames.Seminarraum_45_2_103: Location(9.94611, 48.41944),
    RoomNames.Seminarraum_47_2_101: Location(9.94544, 48.41896),
    RoomNames.Seminarraum_47_2_102: Location(9.94559, 48.41906),
    RoomNames.Seminarraum_47_2_104: Location(9.94574, 48.41918),
    RoomNames.Seminarraum_47_1_504: Location(9.94446, 48.42002),
    RoomNames.Seminarraum_47_1_506: Location(9.94448, 48.42014),
    RoomNames.Seminarraum_47_1_507: Location(9.94453, 48.42007),
    RoomNames.Seminarraum_47_1_508: Location(9.94458, 48.42002),
    RoomNames.Seminarraum_47_2_503: Location(9.94446, 48.42002),
    RoomNames.Seminarraum_47_2_505: Location(9.94448, 48.42014),
    RoomNames.Seminarraum_47_2_506: Location(9.94453, 48.42007),
    RoomNames.Seminarraum_47_2_507: Location(9.94458, 48.42002),
    RoomNames.HH_18_Hörsaal_120: Location(9.96351, 48.42532),
    RoomNames.HH_18_Hörsaal_220: Location(9.96351, 48.42532),
    RoomNames.HH_18_Hörsaal_E20: Location(9.96351, 48.42532),
    RoomNames.HH_18_Hörsaal_E60: Location(9.96351, 48.42532),
    RoomNames.HH_22_Praktikumsraum_1_41: Location(9.96308, 48.42582),
    RoomNames.HH_22_Seminarraum_1_42: Location(9.96308, 48.42582),
    RoomNames.HH_22_Seminarraum_E_03: Location(9.96308, 48.42582),
    RoomNames.HH_22_Seminarraum_E_04: Location(9.96308, 48.42582),
    RoomNames.Hörsaal_E30: Location(9.99279, 48.40997)
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
