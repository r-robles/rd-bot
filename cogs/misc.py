import discord
import psutil
from arsenic import get_session
from arsenic.browsers import Chrome
from arsenic.services import Chromedriver
from datetime import datetime
from discord.ext import commands
from utils.messages import ColoredEmbed, MessageUtils


class Misc(commands.Cog):
    """Miscellaneous commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Pong!
        """
        start = ctx.message.created_at.now()
        message = await ctx.send(content=':ping_pong: Pong!')
        end = datetime.now()
        delta = end - start
        time = delta.microseconds / 1000.0
        await message.edit(content=f':ping_pong: Pong! Time: {time} ms.')

    @commands.command()
    async def botinfo(self, ctx):
        """See some information about the bot.
        """
        bot_user = self.bot.user
        app = await self.bot.application_info()

        cpu_usage = self.bot.process.cpu_percent() / psutil.cpu_count()
        ram_usage = self.bot.process.memory_full_info().uss / 1024 ** 2
        ram_percentage = 100 * \
            (ram_usage / (psutil.virtual_memory().total / 1024 ** 2))

        bot_name = f'{bot_user.name}#{bot_user.discriminator}'
        owner = f'{app.owner.name}#{app.owner.discriminator}'
        num_servers = str(len(self.bot.guilds))
        num_members = str(len(self.bot.users))
        cpu_usage_stat = f'{cpu_usage:.2f}%'
        ram_usage_stat = f'{ram_usage:.2f} MiB ({ram_percentage:.2f}%)'
        uptime = MessageUtils.convert_time_delta(
            datetime.utcnow(), self.bot.startup_time)

        embed = ColoredEmbed()
        embed.set_author(name=bot_name, icon_url=bot_user.avatar_url)
        embed.add_field(name='Owner', value=owner, inline=False)
        embed.add_field(name='Servers', value=num_servers, inline=False)
        embed.add_field(name='Members', value=num_members)
        embed.add_field(name='CPU Usage', value=cpu_usage_stat, inline=False)
        embed.add_field(name='RAM Usage', value=ram_usage_stat, inline=False)
        embed.add_field(name='Uptime', value=uptime, inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=['ss'])
    async def screenshot(self, ctx, link: str):
        """Preview a web page without clicking on it.

        Args:
            link: the link to preview
        """
        if not link.startswith('http://') and not link.startswith('https://'):
            link = 'http://' + link

        service = Chromedriver()
        browser = Chrome(chromeOptions={
            'args': ['--headless', '--disable-gpu', '--window-size=1920,1080']
        })

        async with get_session(service, browser) as session:
            await session.get(link)
            screenshot = await session.get_screenshot()

        screenshot_file = discord.File(screenshot, 'image.png')
        await ctx.send(file=screenshot_file)


def setup(bot):
    bot.add_cog(Misc(bot))
