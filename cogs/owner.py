import asyncio
import json
import sys
from discord.ext import commands


class Owner:
    """Commands restricted to the bot owner."""

    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
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
    async def unload(self, ctx, extension):
        """Unloads an extension."""
        extension = f'cogs.{extension}'
        try:
            self.bot.unload_extension(extension)
        except (AttributeError, ImportError) as ex:
            await ctx.send(f'```py\n{type(ex).__name__}: {str(ex)}\n```')
            return
        await ctx.send(f'{extension} has been successfully unloaded.')

    @commands.command()
    async def bash(self, ctx, command):
        """Run a bash command."""
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        stdout, stderr = await process.communicate()

        if stdout:
            await ctx.send(stdout)
        else:
            await ctx.send(stderr)


def setup(bot):
    bot.add_cog(Owner(bot))
