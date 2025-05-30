import dataclasses

from park_das.car_park_constants import CarParkNames


@dataclasses.dataclass
class CarPark:
    name: CarParkNames
    free_spaces: int

    def __init__(self, name: CarParkNames, left_spaces: int):
        self.name = name
        self.free_spaces = left_spaces

    def get_pos(self) -> (float, float):
        (lat, lon) = self.name.get_pos()
        return lat, lon
