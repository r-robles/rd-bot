import json
import sys
from discord.ext import commands


class Owner:
    """Commands restricted to the bot owner."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, extension):
        """Reloads an extension."""
        extension = f'cogs.{extension}'
        try:
            self.bot.unload_extension(extension)
            self.bot.load_extension(extension)
        except (AttributeError, ImportError) as ex:
            await ctx.send(f'```py\n{type(ex).__name__}: {str(ex)}\n```')
            return
        await ctx.send(f'{extension} has been successfully reloaded.')

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, extension):
        """Loads an extension."""
        extension = f'cogs.{extension}'
        try:
            self.bot.load_extension(extension)
        except (AttributeError, ImportError) as ex:
            await ctx.send(f'```py\n{type(ex).__name__}: {str(ex)}\n```')
            return
        await ctx.send(f'{extension} has been successfully loaded.')

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, extension):
        """Unloads an extension."""
        extension = f'cogs.{extension}'
        try:
            self.bot.unload_extension(extension)
        except (AttributeError, ImportError) as ex:
            await ctx.send(f'```py\n{type(ex).__name__}: {str(ex)}\n```')
            return
        await ctx.send(f'{extension} has been successfully unloaded.')


def setup(bot):
    bot.add_cog(Owner(bot))
