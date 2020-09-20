from collections import Counter
from discord.ext import commands
from database.models.prefix import Prefix
from utils.converters import InsensitiveMemberConverter
from utils.messages import ColoredEmbed, MessageUtils


class Server(commands.Cog):
    """Server related commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def serverinfo(self, ctx):
        """Get information about the server."""
        guild = ctx.guild

        create_time = MessageUtils.stringify_datetime(guild.created_at)
        roles = ', '.join(
            [role.name for role in guild.roles if role.name != '@everyone'])
        guild_info = '\n'.join((f'**ID**: {guild.id}',
                                f'**Owner**: {guild.owner}',
                                f'**Region**: {guild.region}',
                                f'**Created On**: {create_time}',
                                f'**Roles**: {roles}'))

        members = guild.members
        member_counts = Counter(map(lambda m: m.status.name, members))
        member_stats = '\n'.join((f'**Online**: {member_counts["online"]}',
                                  f'**Idle**: {member_counts["idle"]}',
                                  f'**Do Not Disturb**: {member_counts["dnd"]}',
                                  f'**Offline**: {member_counts["offline"]}',
                                  f'**Total**: {len(members)}'))

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        channel_info = '\n'.join((f'**Text**: {text_channels}',
                                  f'**Voice**: {voice_channels}'))

        embed = ColoredEmbed()
        embed.set_author(name=guild, icon_url=guild.icon_url)
        embed.add_field(name='General Info', value=guild_info, inline=False)
        embed.add_field(name='Member Stats', value=member_stats, inline=False)
        embed.add_field(name='Channels', value=channel_info, inline=False)
        embed.set_thumbnail(url=guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def avatar(self, ctx, *, member: InsensitiveMemberConverter = None):
        """Get someone's avatar.

        Args
        ----
        member:
            the member whose avatar you want to get. Defaults to
            yourself if a member is not specified
        """
        if member is None:
            member = ctx.author

        avatar = member.avatar_url_as(static_format='png')

        embed = ColoredEmbed()
        embed.set_author(name=member, icon_url=avatar)
        embed.set_image(url=avatar)
        await ctx.send(embed=embed)

    def _format_status(self, status):
        if status.name == 'dnd':
            return 'Do Not Disturb'
        return status.name.capitalize()

    @commands.command()
    @commands.guild_only()
    async def userinfo(self, ctx, *, member: InsensitiveMemberConverter = None):
        """Get information about a user.

        Args
        ----
        member:
            the member to get information about. Defaults to yourself
            if a member is not specified
        """
        if member is None:
            member = ctx.author

        status = self._format_status(member.status)
        join_time = MessageUtils.stringify_datetime(member.joined_at)
        register_time = MessageUtils.stringify_datetime(member.created_at)
        activity = member.activity.name if member.activity else 'None'
        roles = ", ".join(
            [r.name for r in member.roles if r.name != '@everyone']) or 'None'
        user_info = '\n'.join((f'**Username**: {member}',
                               f'**Nickname**: {member.nick}',
                               f'**ID**: {member.id}',
                               f'**Status**: {status}',
                               f'**Activity**: {activity}',
                               f'**Joined On**: {join_time}',
                               f'**Registered On**: {register_time}',
                               f'**Roles**: {roles}'))

        embed = ColoredEmbed()
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        embed.add_field(name='General Info', value=user_info, inline=False)
        await ctx.send(embed=embed)

    @commands.group(case_insensitive=True)
    async def prefix(self, ctx):
        """Manage the prefixes for invoking commands."""
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @prefix.command(name='show')
    async def prefix_show(self, ctx):
        """Show the prefix for this server."""
        await ctx.send(f'The prefix for this server is `{self.bot.prefixes[ctx.guild.id]}`.')

    async def _update_prefix(self, model, prefix, guild_id):
        """Update the database and cache with the new prefix for this server.

        Args
        ----
        model:
            the prefix model to update
        prefix:
            the new prefix for the server
        guild_id:
            the guild id of the server
        """
        await model.update(prefix=prefix).apply()
        self.bot.prefixes[guild_id] = prefix

    @prefix.command(name='update')
    async def prefix_update(self, ctx, prefix: str):
        """Update the prefix for this server.

        If you want your prefix to contain spaces in the middle or end,
        then the prefix should be enclosed in double quotes.

        Required Permissions
        --------------------
        Manage Guild

        Args
        ----
        prefix:
            the new prefix for this server.
        """
        # Since sent messages are left-stripped of whitespaces, we don't want them to
        # start with whitespaces either.
        new_prefix = prefix.lstrip()

        model = await Prefix.get(ctx.guild.id)
        await self._update_prefix(model, new_prefix, ctx.guild.id)

        await ctx.send(f'The prefix for this server is now updated to `{new_prefix}`.')

    @avatar.error
    @userinfo.error
    async def handle_member_not_found(self, ctx, error):
        """Error handler for members not being found."""
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)


def setup(bot):
    bot.add_cog(Server(bot))
