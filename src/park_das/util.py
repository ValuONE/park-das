import os
import math
from urllib.parse import urlencode
from typing import List, Dict

from telebot.types import Location

from .constants import MapProvider
from .models import CarPark

# https://www.kompf.de/gps/distcalc.html
def haversine_distance(l1 : Location, l2 : Location) -> float:
    """
    Calculate the simple distance between two points on the Earth
    given their latitude and longitude in degrees.

    :param l1: A telegram location
    :param l2: Another telegram location
    :return: Distance in km
    """
    mean_lat = (l1.latitude + l2.latitude) / 2
    mean_lat_rad = math.radians(mean_lat)

    dx = 111.3 * math.cos(mean_lat_rad) * (l1.longitude - l2.longitude)
    dy = 111.3 * (l1.latitude - l2.latitude)

    distance = math.sqrt(dx * dx + dy * dy)
    return distance

def build_routing_data(location : Location, provider : MapProvider) -> Dict[str, str]:
    """
    Create routable link for any map provider

    :param location: Location in telegram format
    :param provider: Selected provider
    :return: Navigation link
    """
    match provider:
        case MapProvider.APPLE:
            return { "url" : _build_applemaps_url(location) }
        case MapProvider.GOOGLE:
            return { "url" : _build_googlemaps_url(location) }
        case _:
            return { "callback_data" : "Provider not set!" }

# https://developers.google.com/maps/documentation/urls/get-started?hl=de#directions-action
def _build_googlemaps_url(location : Location) -> str:
    """
    Creates a routable link to the provided location on Google Maps

    :param location: Location object containing latitude and longitude of the destination
    :return: Routable link to the location on Google Maps
    """
    return "https://www.google.com/maps/dir/?api=1" +\
            f"&destination={location.latitude},{location.longitude}&travelmode=driving"

# https://developer.apple.com/documentation/mapkitjs/adding_a_link_to_your_app
def _build_applemaps_url(location: Location) -> str:
    """
    Creates a routable link to the provided location on Apple Maps

    :param location: Location object containing latitude and longitude of the destination
    :return: Routable link to the location on Apple Maps
    """
    return f"https://maps.apple.com/?daddr={location.latitude},{location.longitude}&dirflg=d"

# https://developers.google.com/maps/documentation/maps-static/start
def static_map(markers: List[CarPark]) -> str:
    """
    Creates link to download a static map using the Google Maps API.
    The map is positioned and zoomed to show the provided locations as color coded markers.

    :param markers: List of objects that contain the location & parking info
    :return: Download link to static map
    """
    try:
        api_key = os.environ["GOOGLEMAPS_API_KEY"]
    except KeyError as e:
        raise ValueError("GOOGLEMAPS_API_KEY environment variable is not set or is empty.") from e

    base = "https://maps.googleapis.com/maps/api/staticmap?"
    params = []
    params.append(("key", api_key))
    params.append(("size", "512x256"))
    params.append(("scale", "2"))
    params.append(("maptype", "roadmap"))
    params.append(("map_id", "44f7ebc46b9403cff2633fe2"))

    for marker in markers:
        loc = marker.get_pos()
        params.append(
            (
                "markers",
                (
                    f"color:{marker.occupancy_level(False)}|"
                    f"label:{markers.index(marker)+1}|"
                    f"{loc.latitude},{loc.longitude}"
                )
            )
        )

    return base + urlencode(params)
