import aiohttp
import random
import discord
from discord.ext import commands

class Fun:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def xkcd(self, ctx):
        """See the latest XKCD comic."""
        async with aiohttp.ClientSession() as session:
            async with session.get('https://xkcd.com/info.0.json') as r:
                if r.status == 200:
                    json = await r.json()
                    embed = discord.Embed(title=json['title'],
                                          description=json['alt'],
                                          color=0xff4d4d)
                    embed.set_image(url=json['img'])
                    await ctx.send(embed=embed)
                session.close()

    @commands.command()
    async def lenny(self, ctx):
        """( ͡° ͜ʖ ͡°)"""
        await ctx.send('( ͡° ͜ʖ ͡°)')

def setup(bot):
    bot.add_cog(Fun(bot))
