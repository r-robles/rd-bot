import random
import discord
from discord.ext import commands
from utils.messages import ColoredEmbed


class Fun:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def xkcd(self, ctx):
        """See the latest XKCD comic."""
        async with self.bot.session.get('https://xkcd.com/info.0.json') as r:
            if r.status == 200:
                json = await r.json()
                embed = ColoredEmbed(title=json['title'],
                                     description=json['alt'])
                embed.set_image(url=json['img'])
                await ctx.send(embed=embed)

    @commands.command()
    async def lenny(self, ctx):
        """( ͡° ͜ʖ ͡°)"""
        await ctx.send('( ͡° ͜ʖ ͡°)')


def setup(bot):
    bot.add_cog(Fun(bot))
