import dataclasses

from park_das.car_park_constants import CarParkNames


@dataclasses.dataclass
class CarPark:
    """
    Represents a car park with a name and the number of available spaces.
    
    Attributes:
        name (CarParkNames): The name of the car park, based on the CarParkNames enum.
        free_spaces (int): The current number of available parking spaces.
    """
    name: CarParkNames
    free_spaces: int

    def __init__(self, name: CarParkNames, left_spaces: int):
        self.name = name
        self.free_spaces = left_spaces

    def get_pos(self) -> (float, float):
        """
       Returns the geographic position (latitude, longitude) of the car park.
    
       Returns:
           tuple[float, float]: A tuple containing the latitude and longitude of the car park.
       """
        (lat, lon) = self.name.get_pos()
        return lat, lon
