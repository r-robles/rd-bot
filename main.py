import datetime
import os
import json
import aiohttp
from discord.ext import commands

config = json.load(open('config.json'))

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.session = aiohttp.ClientSession(loop=self.loop)
        self.config = config
        self.startup_time = datetime.datetime.utcnow()

    async def on_ready(self):
        print(f'You are currently logged in as {bot.user}.')

if __name__ == '__main__':
    bot = Bot(command_prefix='-', config=config)

    for file in os.listdir('cogs'):
        if file.endswith('.py'):
            ext = file[:-3]
            try:
                bot.load_extension(f'cogs.{ext}')
            except Exception as e:
                print(f'Failed to load extension {ext}: {e}')

    bot.run(bot.config['discord'])
