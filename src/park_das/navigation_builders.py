from typing import Tuple

def build_googlemaps_url(location : Tuple[float, float]) -> str:
    """
    Erstellt navigierbaren Google Maps Link

    Args:
        target (location) : Lat & Lon
    Returns:
        str: Google Maps Link
    """
    # https://developers.google.com/maps/documentation/urls/get-started?hl=de#directions-action
    return f"https://www.google.com/maps/dir/?api=1&destination={location[0]},{location[1]}&travelmode=driving"
