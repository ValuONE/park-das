import math

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