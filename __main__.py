import asyncio
import logging
import sys
import i18n

from src.park_das.monkey_patch import aioschedule
from src.park_das.scrapper import fetch_data
from src.park_das.handlers import bot
from src.park_das import voice_support # pylint: disable=unused-import
from src.park_das.constants import UserLanguage
from src.park_das import output_support

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logging.getLogger("telebot").setLevel(logging.DEBUG)

# Set translation data
i18n.load_path.append("./i18n")

# No namespace
i18n.set(
    "filename_format",
    "{locale}.{format}"
)

# Raise error if translation is missing
i18n.set(
    "on_missing_translation",
    "error"
)

# Set available languages
i18n.set(
    "available_locales",
    [str(lang) for lang in UserLanguage if lang != UserLanguage.UNDEFINED]
)

async def scheduler():
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def main():
    await bot.setup_bot()

    await aioschedule.every(1).minute.do(fetch_data).run()
    await asyncio.gather(bot.api.polling(), scheduler())


if __name__ == "__main__":
    asyncio.run(main())
