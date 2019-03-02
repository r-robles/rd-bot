import discord
from discord.ext import commands
from utils.converters import ReasonConverter


class Mod(commands.Cog):
    """Commands for managing the server."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, ctx, user: discord.Member, *, reason: ReasonConverter = None):
        """Kick a user from the server.

        The person to kick must be in a role that is lower in the
        hierarchy than BOTH the command invoker AND the bot.

        Required Permissions:
            Kick Members

        Args:
            member: the member to kick
            reason: the reason for kicking the member
        """
        if user.top_role >= ctx.author.top_role:
            await ctx.send('You cannot kick someone with a higher role than you.')
            return
        if user.top_role >= ctx.me.top_role:
            await ctx.send('Unable to kick user. That user has a higher role than me.')
            return

        if reason is None:
            reason = f'Kicked by {ctx.author} ({ctx.author.id}). No reason specified.'
        await user.kick(reason=reason)
        await ctx.send(f'{user.name} has been kicked from the server.')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx, user: discord.Member, *, reason: ReasonConverter = None):
        """Ban a user from the server.

        The person to ban must be in a role that is lower in the
        hierarchy than BOTH the command invoker AND the bot.

        Required Permissions:
            Ban Members

        Args:
            member: the member to ban
            reason (optional): the reason for banning the member
        """
        if user.top_role >= ctx.author.top_role:
            await ctx.send('You cannot ban someone with a higher role than you.')
            return
        if user.top_role >= ctx.me.top_role:
            await ctx.send('Unable to ban user. That user has a higher role than me.')
            return

        if reason is None:
            reason = f'Banned by {ctx.author} ({ctx.author.id}). No reason specified.'
        await user.ban(reason=reason)
        await ctx.send(f'{user.name} has been banned from the server.')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx, limit: int = 10):
        """Delete the last few messages.

        Required Permissions:
            Manage Messages

        Args:
            limit: number of messages to delete, which must be between 0 and 500
        """
        if limit < 0 or limit > 500:
            await ctx.send('You can only purge a maximum of 500 messages.')
            return

        messages_deleted = await ctx.channel.purge(limit=limit, before=ctx.message)
        await ctx.send(f'Deleted {len(messages_deleted)} message(s)!', delete_after=10)
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Mod(bot))
