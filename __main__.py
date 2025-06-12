import asyncio
import aioschedule

import i18n

from src.park_das.scrapper import fetch_data
from src.park_das.handlers import bot

i18n.load_path.append("./i18n")
i18n.set('filename_format', '{locale}.{format}')
i18n.set("on_missing_translation", "error")
i18n.set("available_locales", ["en", "de"])

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
