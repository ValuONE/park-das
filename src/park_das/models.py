import dataclasses
from typing import Tuple

from .constants import CarParkNames


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
    total_spaces: int

    def get_pos(self) -> Tuple[float, float]:
        """
       Returns the geographic position (latitude, longitude) of the car park.
    
       Returns:
           tuple[float, float]: A tuple containing the latitude and longitude of the car park.
       """
        (lat, lon) = self.name.get_pos()
        return lat, lon
