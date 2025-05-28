from src.park_das.bot import ParkBot
from src.park_das.handlers import *

if __name__ == "__main__":
    ParkBot().setup()
    ParkBot().bot.infinity_polling()