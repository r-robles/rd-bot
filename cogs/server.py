from collections import Counter
from discord.ext import commands
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

    @prefix.command(name='list')
    async def prefix_list(self, ctx):
        """List the prefixes for this server."""
        prefixes = map(lambda x: f'`{x}`', self.bot.prefixes[ctx.guild.id])
        await ctx.send(f'Here are the prefixes for this server:\n{", ".join(prefixes)}')

    async def _update_prefixes(self, guild_id, prefixes):
        """Update the database and cache with the new prefixes for the guild.

        Args
        ----
        guild_id: int
            the id of the guild to update
        prefixes: str[]
            the updated list of prefixes
        """
        query = "update prefixes set prefixes = $1 where guild_id = $2;"
        await self.bot.database.execute(query, prefixes, guild_id)

        self.bot.prefixes[guild_id] = prefixes

    @commands.has_permissions(manage_guild=True)
    @prefix.command(name='add')
    async def prefix_add(self, ctx, prefix: str):
        """Add a new prefix to this server.

        If you want your prefix to contain spaces in the middle or end,
        then the prefix should be enclosed in double quotes.

        Required Permissions
        --------------------
        Manage Guild

        Args
        ----
        prefix:
            the prefix to add
        """
        prefix_to_add = prefix.lstrip(' ')

        guild_id = ctx.guild.id
        current_prefixes = self.bot.prefixes[guild_id]

        if prefix_to_add in current_prefixes:
            return await ctx.send(f'`{prefix}` is already a prefix for this server!')
        if len(prefix_to_add) == 0:
            return await ctx.send(f'You must enter a prefix to add!')

        current_prefixes.append(prefix_to_add)
        await self._update_prefixes(guild_id, current_prefixes)

        formatted_prefixes = map(lambda x: f'`{x}`', current_prefixes)
        await ctx.send(f'Here are the new prefixes for this server:\n{", ".join(formatted_prefixes)}')

    @commands.has_permissions(manage_guild=True)
    @prefix.command(name='remove', aliases=['delete'])
    async def prefix_remove(self, ctx, prefix: str):
        """Remove a prefix from this server.

        For prefixes that contain spaces in the middle or at the end,
        enclose the prefix in double quotes.

        Required Permissions
        --------------------
        Manage Guild

        Args
        ----
        prefix:
            the prefix to remove
        """
        guild_id = ctx.guild.id
        current_prefixes = self.bot.prefixes[guild_id]

        if prefix not in current_prefixes:
            return await ctx.send(f'`{prefix}` is not a prefix for this server!')
        if len(current_prefixes) == 1:
            return await ctx.send(f'You must have at least 1 prefix remaining for this server.')

        current_prefixes.remove(prefix)
        await self._update_prefixes(guild_id, current_prefixes)

        formatted_prefixes = map(lambda x: f'`{x}`', current_prefixes)
        await ctx.send(f'Here are the new prefixes for this server:\n{", ".join(formatted_prefixes)}')

    @avatar.error
    @userinfo.error
    async def handle_member_not_found(self, ctx, error):
        """Error handler for members not being found."""
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)


def setup(bot):
    bot.add_cog(Server(bot))
