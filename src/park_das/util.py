import os
import math

from json import loads, dumps, JSONDecodeError
from urllib.parse import urlencode
from typing import List, Any, Tuple, Dict

from telebot.types import Location

from .constants import MapProvider, Callbacks
from .models import ParkingLot

def check_json(data: str | bytes) -> bool:
    """
    Check data for valid JSON

    :param data: Data as string or bytes
    :return: Flag if data is valid JSON
    """
    if not isinstance(data, (str, bytes)):
        return False
    try:
        json_data = loads(data)
        return json_data is not None
    except (JSONDecodeError, ValueError):
        return False

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
            return { "callback_data" : dumps({"type":Callbacks.MAP_PROVIDER_ERROR}) }

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
def static_map(markers: List[ParkingLot] | None = None, path: str | None = None) -> str:
    """
    Creates link to download a static map using the Google Maps API.
    The map is positioned and zoomed to show the provided locations as color coded markers.
    Alternatively or additionally, an encoded path is drawn on the map.

    :param markers: List of objects that contain the location & parking info, defaults to None
    :param path: Encoded path to be displayed, defaults to None
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

    if markers is None and path is None:
        raise ValueError("Neither markers nor path are provided!")
    if markers is not None:
        for marker in markers:
            params.append(("markers", marker.to_map_marker(markers.index(marker) + 1)))
    if path is not None:
        params.append(("path", f"enc:{path}"))

    return base + urlencode(params)

# https://developers.google.com/maps/documentation/routes/compute_route_directions
def routing_request(
    origin: Location,
    destination: Location,
    lang: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Builds a google maps API request for provided origin and destination in provided language

    :param origin: Origin Telegram location
    :param destination: Target Telegram location
    :param lang: Language the directions should be in
    :return: Tuple containing the link and request data (json)
    """
    data = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": origin.latitude,
                    "longitude": origin.longitude
                },
                "heading": 0 if origin.heading is None else origin.heading
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": destination.latitude,
                    "longitude": destination.longitude
                }
            }
        },
        "travelMode": "DRIVE",
        "computeAlternativeRoutes": False,
        "languageCode": lang
    }

    try:
        api_key = os.environ["GOOGLEMAPS_API_KEY"]
    except KeyError as e:
        raise ValueError("GOOGLEMAPS_API_KEY environment variable is not set or is empty.") from e

    base = "https://routes.googleapis.com/directions/v2:computeRoutes?"

    params = []
    params.append(("key", api_key))
    params.append(("fields", "*"))

    return (base + urlencode(params), data)
