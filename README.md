# 🚗 ParkDas – Multimodal Parking Assistant for Ulm University

[![Lint](https://github.com/ValuONE/park-das/actions/workflows/lint.yml/badge.svg?branch=dev)](https://github.com/ValuONE/park-das/actions/workflows/lint.yml)
[![Python 3.10](https://img.shields.io/badge/python-3.10-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/release/python-3100/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)](https://core.telegram.org/bots)

ParkDas is a Telegram bot that helps students, employees and visitors find a free parking spot at
**Ulm University** and in **Ulm's city centre**. It pulls live occupancy data from public parking guidance
systems and answers through text, buttons, maps, location sharing and voice, in **German** or **English**.

The project was built for the course *Multimodale Benutzerschnittstellen* (Multimodal User Interfaces)
at Ulm University in the 2025 summer semester.

## ✨ Features

| Command | What it does |
|---|---|
| `/start` | Starts or resets the bot and shows the welcome and help messages. |
| `/help` | Lists all available commands. |
| `/overview` | Shows every parking lot on a map with its current occupancy, split into campus and city. |
| `/navigation` | Shows a map of lots that still have free spaces, with one navigation button per lot. |
| `/recommend` | Recommends the closest lot that isn't full, based on your current location or a room you name (e.g. *"Is there a parking spot near O27?"*). |
| `/timer` | Schedules a recommendation for a later time, optionally for a specific room (e.g. *"I'll be at H20 tomorrow at 9"*). Can also reschedule or cancel. |
| `/automatic` | Explains how to share your **live location**. The bot then sends a recommendation automatically when you get close to campus. |
| `/settings` | Sets language, map provider (Google / Apple Maps), user type and output type. |

### Multimodal interaction

- **Natural-language input:** you don't need slash commands. Free text is mapped to the right command by
  Google Gemini, which also pulls out times and known rooms (lecture halls, seminar rooms and clinics) from
  the message.
- **Voice input:** Telegram voice messages are transcribed locally with
  [OpenAI Whisper](https://github.com/openai/whisper) and then handled like text input.
- **Voice output:** with output type *Voice*, replies are read aloud with
  [gTTS](https://github.com/pndurette/gTTS).
- **Maps and navigation:** static maps with colour-coded markers (Google Static Maps API), plus deep links
  that open Google Maps or Apple Maps.
- **Location awareness:** one-off location sharing for instant recommendations, and live location with a
  proximity alert for automatic ones.
- **User types:** *Visitor*, *Employee* and *Inner city* each see the parking lots that are relevant to them.

## 🏗️ Architecture

```
__main__.py                 Entry point: i18n setup, scheduler, bot polling
src/park_das/
├── bot.py                  ParkBot wrapper around the async Telegram API (commands, live locations, timers)
├── handlers.py             Telegram handlers for all commands, locations, free text and voice
├── message_analyser.py     Gemini-based intent classification and time/location extraction
├── voice_support.py        Speech-to-text with Whisper (OGG → WAV via ffmpeg)
├── output_support.py       Text-to-speech output with gTTS
├── scrapper.py             Scrapes live parking data every minute with crawl4ai
├── models.py               Data models and SQLite-backed user settings (aiosqlite)
├── constants.py            Parking lots, rooms, settings enums, commands
├── util.py                 Distance calculation, Google Maps URLs, routing helpers
└── monkey_patch.py         Small patches for third-party libraries
i18n/                       German and English translations (de.yml, en.yml)
assets/                     Images used by the bot
```

**Data sources**

- Ulm University parking guidance system (visitor and employee views)
- [PBW](https://www.pbw.de/) parking finder (Parkhaus Helmholtzstraße)

## 🚀 Getting started

### Prerequisites

- **Python 3.10** (the project pins `~3.10`)
- [**Poetry**](https://python-poetry.org/) for dependency management
- [**ffmpeg**](https://ffmpeg.org/) on your `PATH` (needed for voice messages)
- A **Telegram bot token** from [@BotFather](https://t.me/BotFather)
- A **Google API key** with these APIs enabled:
  - Maps Static API
  - Routes API
  - Generative Language API (Gemini)

### Installation

```bash
git clone https://github.com/ValuONE/park-das.git
cd park-das

# Install dependencies
poetry install

# Install the headless browser used by crawl4ai
poetry run crawl4ai-setup
```

### Configuration

Configuration is done with environment variables:

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_TOKEN` | ✅ | Token of your Telegram bot |
| `GOOGLEMAPS_API_KEY` | ✅ | Google API key, used for Maps **and** Gemini |
| `GOOGLEMAPS_MAP_ID` | ❌ | Map ID for a custom map style (from the Google Cloud Console). If it isn't set, the default Google style is used. |
| `WHISPER_MODEL_SIZE` | ❌ | Whisper model: `tiny` (default), `base`, `small`, `medium` or `large` |

### Running the bot

Start the bot from the repository root, because translations and assets are loaded with relative paths:

```bash
poetry run python __main__.py
```

The bot registers its commands with Telegram, fetches parking data every minute and starts polling.
User settings are stored in a local SQLite file, `settings.db`.

> 💡 Run the bot on **Linux or macOS** (on Windows, use WSL). Some parts rely on POSIX behaviour, such as
> the ffmpeg call for voice messages and the date formatting for timers.

## 🧹 Code quality

The project is linted with **Pylint** (configuration in `.pylintrc`).

```bash
poetry run pylint "**/*.py"
```

## 🌍 Translations

All user-facing text is in `i18n/de.yml` and `i18n/en.yml`. To add a language:

1. Copy one of the files to `i18n/<locale>.yml` and translate the strings.
2. Add the locale to the `UserLanguage` enum in `src/park_das/constants.py`.

Missing translations raise an error on purpose, so incomplete language files are caught early.

## ⚠️ Limitations

- The parking data is scraped from public websites. If their HTML layout changes, the scraper may break.
- The list of parking lots and rooms is specific to Ulm University and Ulm's city centre.

## 👥 Authors

- Alexander Epple
- Dennis Itzel
- Valentin Piendl

Developed as a student project at **Ulm University**.
