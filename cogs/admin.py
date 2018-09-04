import asyncpg
import discord
from discord.ext import commands


class Admin:
    """Commands restricted to administrators and server managers."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def prefix(self, ctx):
        if ctx.invoked_subcommand is None:
            help_command = self.bot.get_command('help')
            await ctx.invoke(help_command, command='prefix')

    @prefix.command(name='list')
    async def prefix_list(self, ctx):
        """Lists the prefixes for this server."""
        prefixes = self.bot.prefixes[ctx.guild.id]
        return await ctx.send(f'Here are the prefixes for this guild:\n{", ".join(prefixes)}')

    @commands.has_permissions(manage_guild=True)
    @prefix.command(name='add')
    async def prefix_add(self, ctx, *, prefix):
        """Adds a new prefix for this server."""
        guild_id = ctx.guild.id
        current_prefixes = self.bot.prefixes[guild_id]

        if prefix in current_prefixes:
            return await ctx.send(f'{prefix} is already a prefix for this server!')

        current_prefixes.append(prefix)
        connection = await self.bot.database.acquire()
        async with connection.transaction():
            query = "update prefixes set prefixes = $1 where guild_id = $2;"
            await connection.execute(query, current_prefixes, guild_id)
        await self.bot.database.release(connection)

        self.bot.prefixes[guild_id] = current_prefixes

        return await ctx.send(f'Here are your new guild prefixes:\n{", ".join(current_prefixes)}')

    @commands.has_permissions(manage_guild=True)
    @prefix.command(name='remove', aliases=['delete'])
    async def prefix_remove(self, ctx, *, prefix):
        """Removes a prefix from this server."""
        guild_id = ctx.guild.id
        current_prefixes = self.bot.prefixes[guild_id]

        if prefix not in current_prefixes:
            return await ctx.send(f'{prefix} is not a prefix for this server!')
        if len(current_prefixes) == 1:
            return await ctx.send(f'You must have at least 1 prefix remaining for this server.')

        current_prefixes.remove(prefix)
        connection = await self.bot.database.acquire()
        async with connection.transaction():
            query = "update prefixes set prefixes = $1 where guild_id = $2;"
            await connection.execute(query, current_prefixes, guild_id)
        await self.bot.database.release(connection)

        self.bot.prefixes[guild_id] = current_prefixes

        return await ctx.send(f'Here are your new guild prefixes:\n{", ".join(current_prefixes)}')


def setup(bot):
    bot.add_cog(Admin(bot))
