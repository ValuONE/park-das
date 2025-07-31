import os

from datetime import datetime

import dateparser

from pydantic import BaseModel, Field, ValidationError

from google import genai
from google.genai import types

import i18n

from .models import TimedRecommendation
from .constants import RoomNames, BotCommands


_genai_client = genai.Client(
    api_key=os.environ["GOOGLEMAPS_API_KEY"],
    http_options=types.HttpOptions(api_version='v1beta')
)


#pylint: disable=too-few-public-methods
class _ParsedTimeAndLocation(BaseModel):
    time_estimate: str | None = Field(
        description=(
            "The best time estimate as a string in ISO 8601 format,"
            "or None if the message did not contain time information."
        ),
        default=None
    )
    location: RoomNames = Field(
        description=(
            "An enum value that describes a known location, such as a building, room"
            "or RoomNames.UNDEFINED if the message did not contain location information."
        ),
        default=RoomNames.UNDEFINED
    )
    cancel: bool = Field(
        description=(
            "A flag is True if there is intend about cancelling a timer / reminder,"
            "or False if the intend is unclear or not to cancel a timer / reminder."
        ),
        default=False
    )
#pylint: enable=too-few-public-methods


async def parse_command(message_text : str | None) -> BotCommands:
    """
    Parses user intent (command) from recieved text or transcribed audio.

    :param message_text: Text as string, recieved from a user
    :return: Command that best matches the intent of the user
    """
    if message_text is None:
        return BotCommands.UNKNOWN

    command_conf = types.GenerateContentConfig(
        system_instruction="""
        You are a helpful parking assistant for Ulm University, helping anyone to find parking spaces.
        Your task is to take the users input and determine which command the user wants to execute.
        The task is exclusive, so only choose one command from the commands below.
        If the text cannot be classified into any of the provided commands, use the command 'UNKNOWN'.
        Below are definitions of each command to help aid you in correctly classifying the text.
        Assume these definitions are written by an expert and follow them closely.

        Here are the available commands and their descriptions:

        Navigation: Sends an interactive map of recommended parking lots, which the user can use to navigate to a parking spot.
        Timer: Controls scheduled parking recommendations to be sent at a given time, optionally for specific locations.
        Automatic: Explains how to set up automatic parking recommendations, which are sent each time the user arrives on location.
        Recommend: Recommends the best parking lot close to the user's current location, or a location the user explicitly specified.
        Overview: Shows all existing parking lots on a map, with occupancy level, regardless of the user's location.
        Unknown: Catch-all, asks user for clarification if no other command matches.

        Here are a few examples prompts for each command:

        Navigation:
            - "Where are available parking lot?"
            - "I need directions, where can I park?"
            - "Which options for parking do I have on campus?"
        Timer:
            - "I will be on campus in 15 minutes."
            - "Tomorrow morning I will be in Ulm around 9."
            - "I need a parking spot when I arrive in half an hour."
            - "Cancel my recommendation tomorrow."
            - "I will arrive 10 minutes later."
        Automatic:
            - "Can you send me parking recommendations automatically?"
            - "I would like a parking recommendation when I get there."
            - "Always send a parking recommendation when I arrive on campus."
        Recommend:
            - "I need a good parking spot."
            - "Is there a parking spot near O27?"
            - "Where is my best option to park currently?"
        Overview:
            - "How full are the parking spots currently?"
            - "Show me all options for parking on campus."
            - "What is the parking situation like currently?"
        Unknown:
            - "How is the weather today?"
            - "Where can I pay for my parking ticket?"
            - "Remind me, where did I parked my car again?"
        """,
        response_mime_type="application/json",
        response_schema=BotCommands,
        temperature=0
    )

    response = await _genai_client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=message_text,
        config=command_conf
    )

    return BotCommands.parse(response.text)


async def parse_time_location(
    message_text : str | None,
    existing_timer : TimedRecommendation
) -> TimedRecommendation:
    """
    Parses time and location from recieved text or transcribed audio.

    :param message_text: Text as string, recieved from a user
    :param existing_timer: Existing recommendation for user
    :raises ValueError: Raised if LLM did not process the message
    :return: Recommendation, either containing datetime, location or both
    """

    if message_text is None:
        return existing_timer

    command_conf = types.GenerateContentConfig(
        system_instruction=f"""
        You are an expert time parsing system, combining time information in messages into timestamps.
        Your task is to extract and parse any date and time information from the message that will follow.

        The dates and times may appear in various formats, including but not limited to
        'DD/MM', 'DD-MM', 'DD.MM.', and times in 'HH', 'HH:MM' format.
        Also consider common date phrases like 'yesterday', 'today', 'tomorrow' and 'next week',
        and common time phrases such as 'soon', 'in 10 minutes', 'in the morning' and 'in about an hour'.

        For the identified date and time, convert it into a standardized format (ISO 8601 format, i.e., 'YYYY-MM-DDTHH:MM:SS').
        Use reasonable estimates for missing information, such as the current day if no date was given.
        For relative dates or times, the current time is {datetime.now().isoformat(timespec='minutes')}.

        If there is no time information in the message at all, the timestamp can be None.

        Additionally, you also extract location information if it is present.
        The locations could be rooms such as "O25", "N24 room 227" or "Lecture hall H20",
        or buildings such as "University West", "Administration".
        If there clearly is location information present which cannot be matched directly,
        then use your best judgement to determine a best match.

        If no location information is present, the location should be RoomNames.UNDEFINED.

        If the message signals intent to cancel a scheduled event, the cancel flag should be set.

        If the message signals intend to change a scheduled event, update it accordingly.
        Only change the fields that have been changed and return the others as they were.
        The current scheduled event is {existing_timer.date_time.isoformat(timespec='minutes')
        if existing_timer.date_time is not None else "not set"} for the location {existing_timer.location.name}.

        Here are some examples of the expected output ("message": "timestamp", "location", "cancel"):

        "I will be on campus in half an hour":
            "2025-06-16T10:26:00", "RoomNames.UNI_OST", "False" (assuming it is 2025-06-16T09:56:00)
        "I need a parking spot near H20 tomorrow morning":
            "2025-06-15T09:00:00", "RoomNames.O27_H20", "False" (assuming it is 2025-06-14T17:30:00)
        "Send me recommendations when I arrive at ten":
            "2025-06-13T10:00:00", "RoomNames.UNDEFINED", "False" (assuming it is 2025-06-13T08:30:00)
        "I should arrive in 15 minutes":
            "2025-06-10T07:57:00", "RoomNames.UNDEFINED", "False" (assuming it is 2025-06-10T07:42:00)
        "I need a parking spot for my exercise in 2103 in 20 minutes":
            "2025-06-08T14:24:00", "RoomNames.N25_SEMINARRAUM_2103", "False" (assuming it is 2025-06-08T14:04:00)
        "Actually, I will arrive 10 minutes later"
            "2025-06-19T14:17:00", "RoomNames.UNI_OST", "False" (assuming existing scheduled event "2025-06-19T14:07:00", "RoomNames.UNI_OST")
        "What's the wheater like in Ulm":
            "None", "RoomNames.UNDEFINED", "False"
        "Cancel the recommendation":
            "None", "RoomNames.UNDEFINED", "True"
        "I do not want to be sent a recommendation":
            "None", "RoomNames.UNDEFINED", "True"
        """,
        response_mime_type="application/json",
        response_schema=_ParsedTimeAndLocation,
        temperature=0
    )

    response = await _genai_client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=message_text,
        config=command_conf
    )

    parsed = _ParsedTimeAndLocation.model_construct()

    try:
        parsed = _ParsedTimeAndLocation.model_validate_json(response.text) # type: ignore
    except ValidationError as e:
        raise ValueError("Gemini response empty or incorrect!") from e

    # Cancel existing timer -> Return empty
    if parsed.cancel:
        return TimedRecommendation()

    # Reuse old location if not specified
    location =  parsed.location\
                if parsed.location != RoomNames.UNDEFINED\
                else existing_timer.location

    # Reuse old datetime if not specified
    date_time = dateparser.parse(parsed.time_estimate, languages=i18n.get("available_locales"))\
                if parsed.time_estimate is not None\
                else existing_timer.date_time

    return TimedRecommendation(date_time, location)


async def test():
    test_sentences = [
        "Ich werde um 11:30 in Ulm sein",
        "Ich suche nach einem Parkplatz in der Nähe von O27 und bin in 10 Minuten dort.",
        "Am kommenden Dienstag brauche ich einen Parkplatz am Mittag",
        "Ich brauche in einer halben Stunde einen Parkplatz am Campus",
        "Wo ist der nächste freie Parkplatz?",
        "Wie ist die aktuelle Parksituation?",
        "Wie kannst du mir helfen?",
        "Wie ist das Wetter in Ulm?"
    ]

    for t in test_sentences:
        dt = await parse_time_location(t, TimedRecommendation())
        print(dt)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
