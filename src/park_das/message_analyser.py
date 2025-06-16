import os

from enum import Enum

from google import genai
from google.genai import types

_genai_client = genai.Client(
    api_key=os.environ["GOOGLEMAPS_API_KEY"],
    http_options=types.HttpOptions(api_version='v1beta')
)

class BotCommands(Enum):
    NAVIGATION = "Navigation"
    TIMING = "Timing"
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
            - "Show me where can I park."
            - "Guide me to a good parking spot."
            - "Which options for parking do I have [in the inner city|on campus]?"
        Timing:
            - "I will be on campus in 15 min."
            - "Tomorrow morning I will be in Ulm around 9."
            - "I need a parking spot when I arrive in half an hour."
        Live:
            - "Where can I park nearby?"
            - "Is there a parking spot near O27?"
            - "What is my best to park currently?"
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
        command = await parse_command(t)
        print(command)
