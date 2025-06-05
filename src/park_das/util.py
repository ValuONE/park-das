import math

from telebot.types import Location
from .constants import MapProvider

def simple_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the simple distance between two points on the Earth
    given their latitude and longitude in degrees.
    https://www.kompf.de/gps/distcalc.html
    """
    mean_lat = (lat1 + lat2) / 2
    mean_lat_rad = math.radians(mean_lat)

    dx = 111.3 * math.cos(mean_lat_rad) * (lon1 - lon2)
    dy = 111.3 * (lat1 - lat2)

    distance = math.sqrt(dx * dx + dy * dy)
    return distance

def build_routing_data(location : Location, provider : MapProvider):
    match provider:
        case MapProvider.APPLE:
            return { "url" : _build_applemaps_url(location) }
        case MapProvider.GOOGLE:
            return { "url" : _build_googlemaps_url(location) }
        case _:
            return { "callback_data" : "Provider not set!" }

def _build_googlemaps_url(location : Location) -> str:
    """
    Creates a routable link to the provided location on Google Maps

    :param location: Location object containing latitude and longitude of the destination
    :return: Routable link to the location on Google Maps
    """

    # https://developers.google.com/maps/documentation/urls/get-started?hl=de#directions-action
    return "https://www.google.com/maps/dir/?api=1" +\
            f"&destination={location.latitude},{location.longitude}&travelmode=driving"

def _build_applemaps_url(location: Location) -> str:
    """
    Creates a routable link to the provided location on Apple Maps

    :param location: Location object containing latitude and longitude of the destination
    :return: Routable link to the location on Apple Maps
    """

    # https://developer.apple.com/documentation/mapkitjs/adding_a_link_to_your_app
    return f"https://maps.apple.com/?daddr={location.latitude},{location.longitude}&dirflg=d"
