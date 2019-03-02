import random
from discord.ext import commands


class RNG(commands.Cog):
    """Commands of random chance."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def roll(self, ctx):
        """Roll a six-sided dice.
        """
        num = random.randint(1, 6)
        await ctx.send(f'You rolled a {num}!')

    @commands.command()
    async def flip(self, ctx):
        """Flip a coin.
        """
        flipped = random.choice(['heads', 'tails'])
        await ctx.send(f'You flipped {flipped}!')


def setup(bot):
    bot.add_cog(RNG(bot))
