import asyncio
import aioschedule

from src.park_das.scrapper import fetch_data
from src.park_das.handlers import bot

async def scheduler():
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def main():
    await bot.setup_bot()
    # Hier kann man ansetzten mit dem Caching
    await aioschedule.every(1).minute.do(fetch_data, True).run()
    await asyncio.gather(bot.api.polling(), scheduler())

if __name__ == "__main__":
    asyncio.run(main())
