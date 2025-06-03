def emojify(free, total):
    ratio = free / total
    if ratio > 0.25:
        return "✅"
    if 0.05 < ratio < 0.25:
        return "⚠️"
    return "❌"

def format_car_park(park):
    """
    Formats a car park's information into a string.

    Args:
        park (CarPark): The car park to format.

    Returns:
        str: A formatted string containing the car park's name, free spaces and a status icon.
    """
    return (f"{park.name.value}: {park.free_spaces} frei | "
            f"{emojify(park.free_spaces, park.total_spaces)}\n")
