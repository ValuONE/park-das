import os

from enum import Enum
from datetime import datetime
from dataclasses import dataclass

import dateparser

from pydantic import BaseModel, Field, ValidationError
from google import genai
from google.genai import types

import i18n

_genai_client = genai.Client(
    api_key=os.environ["GOOGLEMAPS_API_KEY"],
    http_options=types.HttpOptions(api_version='v1beta')
)

class BotCommands(Enum):
    NAVIGATION = "Navigation"
    TIMER = "Timing"
    LIVE = "Live"
    OVERVIEW = "Overview"
    UNKNOWN = "Unknown"

    @classmethod
    def parse(cls, to_parse : str | None):
        if to_parse is None:
            return BotCommands.UNKNOWN
        for com in BotCommands:
            if to_parse.find(com.value) != -1:
                return com
        return BotCommands.UNKNOWN

#pylint: disable=too-few-public-methods
class _ParsedTimeAndLocation(BaseModel):
    time_estimate : str | None = Field(
        description=(
            "The best time estimate as a string in ISO 8601 format,"
            "or None if the message did not contain time information."
        ),
        default=None
    )
    location : str | None = Field(
        description=(
            "A string that contains a location, such as a building, parking spot,"
            "or None if the message did not contain location information."
        ),
        default=None
    )
#pylint: enable=too-few-public-methods

@dataclass
class TimeLocation():
    time : datetime | None = None
    location : str | None = None

async def parse_command(user_txt : str | None) -> BotCommands:
    if user_txt is None:
        return BotCommands.UNKNOWN

    command_conf = types.GenerateContentConfig(
        system_instruction="""
        You are a helpful parking assistant for Ulm University, helping anyone to find parking spaces.
        Your task is to take the users input and determine which command the user wants to execute.
        The task is exclusive, so only choose one command from the commands below.
        If the text cannot be classified into any of the provided commands, use the command 'Unknown'.
        Below are definitions of each command to help aid you in correctly classifying the text.
        Assume these definitions are written by an expert and follow them closely.

        Here are the available commands and their descriptions:

        Navigation: Sends a map of available parking spots which the user can use to navigate to a parking spot.
        Timing: Sends information about parking spot occupancy after a given time, so the user knows where to park on arrival.
        Live: Prompts the user to share their location and recommends spots based on where they are.
        Overview: Lists all parking spots and their occupancy regardless of location as a text message.
        Unknown: Catch-all, asks user for clarification if no other command matches.

        Here are a few examples prompts for each command:

        Navigation:
            - "How can I get to the next best parking spot?"
            - "Guide me to a good parking spot."
            - "Which options for parking do I have [in the inner city|on campus]?"
        Timer:
            - "I will be on campus in 15 min."
            - "Tomorrow morning I will be in Ulm around 9."
            - "I need a parking spot when I arrive in half an hour."
        Live:
            - "Where can I park nearby?"
            - "Is there a parking spot near O27?"
            - "Where is my best option to park currently?"
        Overview:
            - "How full are the parking spots currently?"
            - "Show me all options for parking on campus."
            - "Summarize the current parking situation."
        Unknown:
            - "How is the weather today?"
            - "Where can I pay for my parking ticket?"
            - "Remind me where I parked my car."
        """,
        response_mime_type="application/json",
        response_schema=BotCommands,
        temperature=0
    )

    response = await _genai_client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_txt,
        config=command_conf
    )

    return BotCommands.parse(response.text)

async def parse_time_location(user_txt : str | None) -> TimeLocation:
    if user_txt is None:
        return TimeLocation()

    command_conf = types.GenerateContentConfig(
        system_instruction=f"""
        You are an expert time parsing system, combining time information in messages into timestamps.
        Your task is to extract and parse any date and time information from the following message.

        The dates and times may appear in various formats, including but not limited to
        'DD/MM', 'DD-MM', 'DD.MM.', and times in 'HH', 'HH:MM' format.
        Also consider common date phrases like 'yesterday', 'today', 'tomorrow' and 'next week',
        and common time phrases such as 'in 10 minutes', 'in the morning' and 'in about an hour'.

        For each identified date and time, convert it into a standardized format (ISO 8601 format, i.e., 'YYYY-MM-DDTHH:MM:SS').
        If only a date or only a time is provided, use reasonable estimates for the missing information.
        For relative dates or times, the current time is {datetime.now().isoformat(timespec='minutes')}.

        If there is no time information in the message at all, the output can be None.

        Additionally, you should also extract location information if it is present.
        The locations could be parking spots, such as "P1", "Parkplatz 20" or "Parkhaus Helmholtzstraße",
        or buildings and rooms such as "O25", "N24 room 227" or "Lecture hall H20".
        If no location information or no time information is present, the output can be None instead.

        Here are some examples of the expected output ("message": "timestamp", "location"):

        "I will be on campus in half an hour":
            "2025-06-16T10:26:00", "Campus" (assuming it is 2025-06-16T09:56:00)
        "I need a parking spot near H20 tomorrow morning":
            "2025-06-15T09:00:00", "H20" (assuming it is 2025-06-14T17:30:00)
        "Send me recommendations when I arrive at ten":
            "2025-06-13T10:00:00", "None" (assuming it is 2025-06-13T08:30:00)
        "I should arrive in 15 minutes":
            "2025-06-10T07:57:00", "None" (assuming it is 2025-06-10T07:42:00)
        "I need a parking spot for my exercise in 2103 in 20 minutes":
            "2025-06-08T14:24:00", "2103" (assuming it is 2025-06-08T14:04:00)
        "What's the wheater like in Ulm":
            "None", "None"
        """,
        response_mime_type="application/json",
        response_schema=_ParsedTimeAndLocation,
        temperature=0
    )

    response = await _genai_client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_txt,
        config=command_conf
    )

    parsed = _ParsedTimeAndLocation.model_construct()

    try:
        parsed = _ParsedTimeAndLocation.model_validate_json(response.text)
    except ValidationError as e:
        raise ValueError("Gemini response empty or incorrect!") from e

    if parsed.time_estimate is not None:
        return TimeLocation(
            dateparser.parse(parsed.time_estimate, languages=i18n.get("available_locales")),
            None if parsed.location == "None" else parsed.location
        )

    return TimeLocation()

async def test():
    test_sentences = [
        "Ich werde um 11:30 in Ulm sein",
        "Ich suche nach einem Parkplatz in der Nähe von O27 und bin in 10 Minuten dort.",
        "Am kommenden Dienstag brauche ich einen Parkplatz am Mittag",
        "Wo ist der nächste freie Parkplatz?",
        "Wie ist die aktuelle Parksituation?",
        "Wie kannst du mir helfen?",
        "Wie ist das Wetter in Ulm?"
    ]

    for t in test_sentences:
        dt = await parse_time_location(t)
        print(dt)
