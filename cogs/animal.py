from datetime import datetime
import aiohttp
import discord
from discord.ext import commands

class Animal:
    """Some cute animals."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def cat(self, ctx):
        """Meow!"""
        async with self.bot.session.get('http://random.cat/meow') as r:
            if r.status == 200:
                json = await r.json()
                img = json['file']
                embed = self._create_embed(img)
                await ctx.send(embed=embed)

    @commands.command()
    async def dog(self, ctx):
        """Woof!"""
        img = None
        while not img:
            async with self.bot.session.get('https://random.dog/woof.json') as r:
                if r.status == 200:
                    json = await r.json()
                    img = json['url']
                    # Sometimes the API returns .mp4 files, which
                    # can't be used in embeds.
                    if img.endswith('.mp4'):
                        img = None
                        continue
                    else:                                   
                        embed = self._create_embed(img)
                        await ctx.send(embed=embed)

    def _create_embed(self, img: str):
        embed = discord.Embed(colour=0x117711)
        embed.set_image(url=img)
        return embed

def setup(bot):
    bot.add_cog(Animal(bot))
