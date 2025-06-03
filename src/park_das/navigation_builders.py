from telebot.types import Location

def build_googlemaps_url(location : Location) -> str:
    """
    Creates a routable link to the provided location on Google Maps

    Returns:
        str: Routable link
    """
    # https://developers.google.com/maps/documentation/urls/get-started?hl=de#directions-action
    return "https://www.google.com/maps/dir/?api=1" +\
            f"&destination={location.latitude},{location.longitude}&travelmode=driving"
