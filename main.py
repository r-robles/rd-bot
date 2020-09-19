import asyncio
import configparser
import logging
import asyncpg
from discord.ext import commands
from core.bot import Bot

config = configparser.ConfigParser()
config.read('config.ini')

log = logging.getLogger(__name__)

def set_up_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

async def connect_to_database():
    credentials = config['PostgreSQL']

    database_credentials = {
        "user": credentials['user'],
        "password": credentials['password'],
        "database": credentials['database'],
        "host": credentials['host']
    }

    try:
        return await asyncpg.create_pool(**database_credentials)
    except:
        log.error('Failed to connect to database.')

async def run_bot(config, database):
    bot = Bot(config=config,
              database=database)
    try:
        await bot.start(config['Discord']['token'])
    except KeyboardInterrupt:
        await database.close()
        await bot.logout()

async def main():
    database = await connect_to_database()
    await run_bot(config, database)

if __name__ == '__main__':
    set_up_logging()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
