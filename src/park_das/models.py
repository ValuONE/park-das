import dataclasses

from park_das.constants import ParkingSpaces


@dataclasses.dataclass
class CarPark:
    name: ParkingSpaces
    free_spaces: int

    def __init__(self, name: ParkingSpaces, left_spaces: int):
        self.name = name
        self.free_spaces = left_spaces

    def get_position(self) -> (float, float):
        (lat, lon) = self.name.get_position_by_type()
        return lat, lon
