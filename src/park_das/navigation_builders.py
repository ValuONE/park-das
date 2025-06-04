from telebot.types import Location

def build_googlemaps_url(location : Location) -> str:
    """
    Creates a routable link to the provided location on Google Maps

    :param location: Location object containing latitude and longitude of the destination
    :return: Routable link to the location on Google Maps
    """

    # https://developers.google.com/maps/documentation/urls/get-started?hl=de#directions-action
    return "https://www.google.com/maps/dir/?api=1" +\
            f"&destination={location.latitude},{location.longitude}&travelmode=driving"

def build_applemaps_url(location: Location) -> str:
    """
    Creates a routable link to the provided location on Apple Maps

    :param location: Location object containing latitude and longitude of the destination
    :return: Routable link to the location on Apple Maps
    """

    # https://developer.apple.com/documentation/mapkitjs/adding_a_link_to_your_app
    return f"https://maps.apple.com/?daddr={location.latitude},{location.longitude}&dirflg=d"
