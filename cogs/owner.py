import asyncio
import shlex
import subprocess
from discord.ext import commands
from utils.paginator import CodeBlockPaginator


class Owner(commands.Cog):
    """Commands restricted to the bot owner."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def reload(self, ctx, extension):
        """Reload an extension.

        Args
        ----
        extension:
            the extension to reload
        """
        self.bot.unload_extension(extension)
        self.bot.load_extension(extension)
        await ctx.message.add_reaction('✅')

    @commands.command()
    async def load(self, ctx, extension):
        """Load an extension.

        Args
        ----
        extension:
            the extension to load
        """
        self.bot.load_extension(extension)
        await ctx.message.add_reaction('✅')

    @commands.command()
    async def unload(self, ctx, extension):
        """Load an extension.

        Args
        ----
        extension:
            the extension to unload
        """
        self.bot.unload_extension(extension)
        await ctx.message.add_reaction('✅')

    @commands.command()
    async def bash(self, ctx, *, command):
        """Run a bash command.

        Args
        ----
        command:
            the bash command to invoke
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

        content = CodeBlockPaginator.paginate(ctx, result)
        await content.send_message()

    @reload.error
    @load.error
    @unload.error
    async def extension_load_error(self, ctx, error):
        """Error handler for extension loading."""
        if isinstance(error, commands.CommandInvokeError):
            await ctx.message.add_reaction('❌')
            await ctx.send(f'```{error}```')


def setup(bot):
    bot.add_cog(Owner(bot))
