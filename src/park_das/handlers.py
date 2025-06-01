from telebot import types
from park_das.distance import simple_distance
from .bot import bot
from .scrapper import fetch_data


@bot.api.message_handler(commands=["start"])
def start_handler(message: types.Message):
    with bot as api:
        api.send_message(message.chat.id, "Willkommen bei ParkBot!")
        api.send_message(message.chat.id, help_message())


@bot.api.message_handler(commands=["help"])
def help_handler(message: types.Message):
    with bot as api:
        api.send_message(message.chat.id, help_message())


def help_message() -> str:
    help_txt = "Folgende Befehle sind verfügbar:\n"
    return help_txt + "".join(
        [f"/{cmd.command} : {cmd.description}\n" for cmd in bot.api.get_my_commands()]
    )

@bot.api.message_handler(commands=["live"])
def live_handler(message: types.Message):
    markup = types.ReplyKeyboardMarkup(
        row_width=1, resize_keyboard=True, one_time_keyboard=True
    )
    button_geo = types.KeyboardButton(
        text="📍 Standort senden", request_location=True
    )
    markup.add(button_geo)

    with bot as api:
        api.send_message(
            message.chat.id,
            "Tippe auf „📍 Standort senden“, um mir deine aktuelle Position zu schicken.",
            reply_markup=markup,
        )

@bot.api.message_handler(content_types=["location"])
def location_handler(message: types.Message):
    """
    Receives user's location and returns sorted car parks.
    """
    if not message.location:
        return

    lat = message.location.latitude
    lon = message.location.longitude

    # Gets the parking data
    carparks = fetch_data(is_visitor=True)

    # Calculates distances to each parking slot
    carparks_with_distance = []
    for carpark in carparks:
        park_lat, park_lon = carpark.get_pos()
        distance = simple_distance(lat, lon, park_lat, park_lon)
        carparks_with_distance.append((carpark, distance))

    # Sorts the car slots by distance
    carparks_with_distance.sort(key=lambda x: x[1])

    # creates the response message
    response = "🚗 Nächste Parkplätze:\n\n"
    for carpark, distance in carparks_with_distance:
        response += \
            (
                f"{carpark.name.value}: "
                f"{carpark.free_spaces} frei — "
                f"{distance:.1f} km entfernt\n"
            )

    remove_keyboard = types.ReplyKeyboardRemove()

    # Sends the response message
    with bot as api:
        api.send_message(
            message.chat.id,
            response,
            reply_markup=remove_keyboard
        )
