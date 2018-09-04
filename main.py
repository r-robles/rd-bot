import asyncio
import configparser
import datetime
import os
import aiohttp
import asyncpg
import discord
import psutil
from discord.ext import commands

config = configparser.ConfigParser()
config.read('config.ini')


async def run_bot():
    bot = Bot(command_prefix=get_prefix)

    try:
        await bot.start(config['Discord']['token'])
    except KeyboardInterrupt:
        await bot.database.close()
        await bot.logout()


async def get_prefix(bot, msg):
    guild_id = msg.guild.id

    if msg.guild.id in bot.prefixes:
        return commands.when_mentioned_or(*bot.prefixes[guild_id])(bot, msg)

    connection = await bot.database.acquire()
    async with connection.transaction():
        query = "select prefixes from prefixes where guild_id = $1;"
        prefixes = await bot.database.fetchval(query, guild_id)
        if not prefixes:
            prefixes = ['-']
            query = "insert into prefixes(guild_id, prefixes) values($1, $2);"
            await connection.execute(query, msg.guild.id, prefixes)
    await bot.database.release(connection)

    bot.prefixes[guild_id] = prefixes

    return commands.when_mentioned_or(*prefixes)(bot, msg)


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.session = aiohttp.ClientSession(loop=self.loop)
        self.config = config

        self.process = psutil.Process()
        self.startup_time = datetime.datetime.utcnow()

        self.prefixes = {}

    async def on_ready(self):
        print(f'You are currently logged in as {self.user}.')

        game = discord.Game('-help')
        await self.change_presence(activity=game)

        self.load_extensions()

        await self.setup_database()

    async def setup_database(self):
        credentials = config['PostgreSQL']

        database_credentials = {
            "user": credentials['user'],
            "password": credentials['password'],
            "database": credentials['database'],
            "host": credentials['host']
        }

        self.database = await asyncpg.create_pool(**database_credentials)
        await self.database.execute("create table if not exists prefixes(guild_id bigint PRIMARY KEY, prefixes text[])")

    def load_extensions(self):
        for file in os.listdir('cogs'):
            if file.endswith('.py'):
                ext = file[:-3]
                try:
                    self.load_extension(f'cogs.{ext}')
                except Exception as e:
                    print(f'Failed to load extension {ext}: {e}')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_bot())
