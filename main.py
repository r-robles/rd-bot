import asyncio
import configparser
import logging
import time
import discord
from core.bot import Bot
from database import connect_to_database, disconnect_from_database

config = configparser.ConfigParser()
config.read('config.ini')

log = logging.getLogger(__name__)


def set_up_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    logging.Formatter.converter = time.gmtime


async def run_bot():
    intents = discord.Intents.all()
    bot = Bot(config=config, intents=intents)
    try:
        await bot.start(config['Discord']['token'])
    except KeyboardInterrupt:
        await disconnect_from_database()
        await bot.logout()


async def main():
    await connect_to_database(config['PostgreSQL'])
    await run_bot()

if __name__ == '__main__':
    set_up_logging()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
