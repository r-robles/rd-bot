import discord
from discord.ext import commands


class Mod:
    """Commands for managing the server."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, ctx, user: discord.Member, *, reason=None):
        """Kick a user from the server."""
        if reason is None:
            reason = f'User kicked by {ctx.author}.'
        await user.kick(reason=reason)
        await ctx.send(f'{user.name} has been kicked from the server.')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx, user: discord.Member, *, reason=None):
        """Ban a user from the server."""
        if reason is None:
            reason = f'User banned by {ctx.author}.'
        await user.ban(reason=reason)
        await ctx.send(f'{user.name} has been banned from the server.')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx, limit: int=10):
        """Clean up some messages."""
        if limit < 0 or limit > 500:
            await ctx.send('You can only purge a maximum of 500 messages.')
            return

        messages_deleted = await ctx.channel.purge(limit=limit, before=ctx.message)
        await ctx.send(f'Deleted {len(messages_deleted)} message(s)!', delete_after=10)
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Mod(bot))
