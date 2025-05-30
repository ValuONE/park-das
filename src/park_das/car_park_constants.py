from enum import Enum

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

    def get_pos(self) -> tuple[float, float]:
        return CAR_PARK_LOCATIONS[self]

def get_variant_from_str(value: str) -> CarParkNames:
    for member in CarParkNames:
        if member.value == value:
            return member
    raise KeyError(f"No matching enum member for '{value}' found.")

CAR_PARK_LOCATIONS = {
        CarParkNames.P09: (48.41912, 9.942359),
        CarParkNames.P10: (48.42005, 9.943917),
        CarParkNames.P11: (48.42046, 9.944910),
        CarParkNames.P12: (48.42076, 9.945848),
        CarParkNames.P13: (48.42076, 9.945848),
        CarParkNames.P16: (48.42263, 9.947908),
        CarParkNames.P18: (48.423047, 9.949502),
        CarParkNames.P20: (48.42396, 9.951033),
        CarParkNames.P22: (48.42506, 9.954085),
        CarParkNames.P26: (48.42389, 9.951642),
        CarParkNames.P23: (48.42543, 9.954960),
        CarParkNames.P24: (48.42481, 9.953938),
        CarParkNames.P32: (48.42410, 9.957266),
        CarParkNames.P41: (48.42599, 9.958382),
        CarParkNames.P44: (48.42602, 9.962580),
        CarParkNames.M1: (48.40938, 9.991174),
        CarParkNames.M2: (48.40819, 9.992269),
        CarParkNames.M3: (48.41076, 9.99374),
        CarParkNames.M4: (48.40974, 9.994923)
}
