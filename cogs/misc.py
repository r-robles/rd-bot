from datetime import datetime
from discord.ext import commands

class Misc:
    """Miscellaneous commands."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Pong!"""
        start = ctx.message.created_at.now()
        message = await ctx.send(content=':ping_pong: Pong!')
        end = datetime.now()
        delta = end - start
        time = delta.microseconds / 1000.0
        await message.edit(content=f':ping_pong: Pong! Time: {time} ms.')

def setup(bot):
    bot.add_cog(Misc(bot))
