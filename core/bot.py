import aiohttp
import asyncio
import datetime
import logging
import os
import psutil
import discord
import asyncpg
from discord.ext import commands

log = logging.getLogger(__name__)

async def get_prefix(bot, ctx):
    guild_id = ctx.guild.id

    if guild_id in bot.prefixes:
        return commands.when_mentioned_or(*bot.prefixes[guild_id])(bot, ctx)

    query = 'select prefixes from prefixes where guild_id = $1;'
    prefixes = await bot.database.fetchval(query, guild_id)
    if not prefixes:
        prefixes = ['-']
        query = 'insert into prefixes(guild_id, prefixes) values($1, $2);'
        await bot.database.execute(query, guild_id, prefixes)

    bot.prefixes[guild_id] = prefixes

    return commands.when_mentioned_or(*prefixes)(bot, ctx)


class Bot(commands.Bot):
    def __init__(self, config=None, database=None, *args, **kwargs):
        super().__init__(command_prefix=get_prefix,
                         *args,
                         **kwargs)

        self.session = aiohttp.ClientSession(loop=self.loop)

        self.startup_time = datetime.datetime.utcnow()

        self.prefixes = {}

        self.config = config
        self.database = database

    async def on_ready(self):
        log.info(f'Bot is now online as {self.user}.')

        await self.change_presence(activity=discord.Game('-help'))

        self._load_extensions()

    def _load_extensions(self):
        log.info('Loading extensions.')
        for file in os.listdir('cogs'):
            if file.endswith('.py'):
                ext = file[:-3]
                try:
                    self.load_extension(f'cogs.{ext}')
                except Exception as e:
                    log.error(f'Failed to load extension {ext}: {e}')
        log.info(f'The following extensions are now loaded: {self.extensions.keys()}')
