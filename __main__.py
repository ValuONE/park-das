from src.park_das.bot import bot
from src.park_das.handlers import *

if __name__ == "__main__":
    bot.api.infinity_polling()