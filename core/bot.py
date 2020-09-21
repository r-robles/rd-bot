import aiohttp
import datetime
import logging
import os
import discord
from discord.ext import commands
from database.models.prefix import Prefix

DEFAULT_PREFIX = '-'
log = logging.getLogger(__name__)


async def get_prefix(bot, ctx):
    guild_id = ctx.guild.id

    if guild_id in bot.prefixes:
        return commands.when_mentioned_or(*bot.prefixes[guild_id])(bot, ctx)

    model = await Prefix.get(guild_id)
    if not model:
        prefix = DEFAULT_PREFIX
        model = await Prefix.create(guild_id=guild_id, prefix=prefix)

    bot.prefixes[guild_id] = model.prefix

    return commands.when_mentioned_or(model.prefix)(bot, ctx)


class Bot(commands.Bot):
    def __init__(self, config=None, *args, **kwargs):
        super().__init__(command_prefix=get_prefix,
                         *args,
                         **kwargs)

        self.session = aiohttp.ClientSession(loop=self.loop)

        self.startup_time = datetime.datetime.utcnow()
        self.prefixes = {}
        self.config = config

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
