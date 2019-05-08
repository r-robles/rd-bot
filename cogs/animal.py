from datetime import datetime
from discord.ext import commands
from utils.messages import ColoredEmbed


class Animal(commands.Cog):
    """Some cute animals."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def cat(self, ctx):
        """Get a random picture of a cat."""
        async with self.bot.session.get('http://aws.random.cat/meow') as r:
            if r.status == 200:
                json = await r.json()
                img = json['file']
                embed = self._create_embed(img)
                await ctx.send(embed=embed)

    @commands.command()
    async def dog(self, ctx):
        """Get a random picture of a dog."""
        img = None
        while not img:
            async with self.bot.session.get('https://random.dog/woof.json') as r:
                if r.status == 200:
                    json = await r.json()
                    img = json['url']
                    if img.endswith('.mp4'):
                        img = None
                        continue
                    else:
                        embed = self._create_embed(img)
                        await ctx.send(embed=embed)

    def _create_embed(self, img: str):
        embed = ColoredEmbed()
        embed.set_image(url=img)
        return embed


def setup(bot):
    bot.add_cog(Animal(bot))
