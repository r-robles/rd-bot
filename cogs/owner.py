import asyncio
import json
import shlex
import subprocess
import sys
from discord.ext import commands


class Owner(commands.Cog):
    """Commands restricted to the bot owner."""

    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def reload(self, ctx, extension):
        """Reload an extension.

        This assumes that the file you want to reload is in the "cogs"
        folder.

        Args:
            extension: the extension to reload
        """
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
        """Load an extension.

        This assumes that the file you want to load is in the "cogs"
        folder.

        Args:
            extension: the extension to load
        """
        extension = f'cogs.{extension}'
        try:
            self.bot.load_extension(extension)
        except (AttributeError, ImportError) as ex:
            await ctx.send(f'```py\n{type(ex).__name__}: {str(ex)}\n```')
            return
        await ctx.send(f'{extension} has been successfully loaded.')

    @commands.command()
    async def unload(self, ctx, extension):
        """Load an extension.

        This assumes that the file you want to unload is in the "cogs"
        folder.

        Args:
            extension: the extension to unload
        """
        extension = f'cogs.{extension}'
        try:
            self.bot.unload_extension(extension)
        except (AttributeError, ImportError) as ex:
            await ctx.send(f'```py\n{type(ex).__name__}: {str(ex)}\n```')
            return
        await ctx.send(f'{extension} has been successfully unloaded.')

    @commands.command()
    async def bash(self, ctx, *, command):
        """Run a bash command.

        Args:
            command: the bash command to invoke
        """
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            stdout, stderr = await process.communicate()
        # The above does not work on Windows, so the subprocess module
        # is used instead
        except NotImplementedError:
            process = subprocess.Popen(
                shlex.split(command),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

            loop = self.bot.loop
            stdout, stderr = await loop.run_in_executor(None, process.communicate)

        msg = ctx.message

        if stdout:
            await msg.add_reaction('✅')
            result = stdout.decode('utf-8')
        elif stderr:
            await msg.add_reaction('❌')
            result = stderr.decode('utf-8')

        await ctx.send(f'```{result}```')


def setup(bot):
    bot.add_cog(Owner(bot))
