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
        """Get information about the server.
        """
        guild = ctx.guild

        roles = ', '.join(
            [role.name for role in guild.roles if role.name != '@everyone'])
        num_text_channels = len(guild.text_channels)
        num_voice_channels = len(guild.voice_channels)
        create_time = MessageUtils.stringify_datetime(guild.created_at)

        embed = ColoredEmbed(title=guild.name)
        embed.add_field(name='ID', value=guild.id)
        embed.add_field(name='Owner', value=f'{guild.owner}')
        embed.add_field(name='Server Region', value=guild.region)
        embed.add_field(name='Members', value=guild.member_count)
        embed.add_field(name='Text Channels', value=num_voice_channels)
        embed.add_field(name='Voice Channels', value=num_text_channels)
        embed.add_field(name='Roles', value=roles, inline=False)
        embed.set_footer(text=f'Created on {create_time}')
        embed.set_thumbnail(url=guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def avatar(self, ctx, *, member: InsensitiveMemberConverter = None):
        """Get someone's avatar.

        Args:
            member (optional): the member. Defaults to the invoker if a member is not specified
        """
        if member is None:
            member = ctx.author

        avatar = member.avatar_url_as(static_format='png')

        embed = ColoredEmbed()
        embed.set_author(name=member, icon_url=avatar)
        embed.set_image(url=avatar)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def userinfo(self, ctx, *, member: InsensitiveMemberConverter = None):
        """Get information about a user.

        Args:
            member (optional): the member. Defaults to the invoker if a member is not specified
        """
        if member is None:
            member = ctx.author

        roles = ", ".join(
            [r.name for r in member.roles if r.name != '@everyone']) or 'None'
        join_time = MessageUtils.stringify_datetime(member.joined_at)
        register_time = MessageUtils.stringify_datetime(member.created_at)
        activity = member.activity.name if member.activity else 'None'

        embed = ColoredEmbed()
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_author(name=member, icon_url=member.avatar_url)
        embed.add_field(name='ID', value=member.id)
        embed.add_field(name='Nickname', value=member.nick)
        embed.add_field(name='Join Time', value=join_time)
        embed.add_field(name='Register Time', value=register_time)
        embed.add_field(name='Activity', value=activity, inline=False)
        embed.add_field(name='Roles', value=roles, inline=False)
        await ctx.send(embed=embed)

    @commands.group()
    async def prefix(self, ctx):
        """Manage the prefixes for invoking commands.
        """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @prefix.command(name='list')
    async def prefix_list(self, ctx):
        """List the prefixes for this server.
        """
        prefixes = map(lambda x: f'`{x}`', self.bot.prefixes[ctx.guild.id])
        await ctx.send(f'Here are the prefixes for this server:\n{", ".join(prefixes)}')

    async def _update_prefixes(self, guild_id, prefixes):
        """Update the database and cache with the new prefixes for the guild.

        Args:
            guild_id (int): the id of the guild to update
            prefixes (str[]): the updated list of prefixes
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

        Required Permissions:
            Manage Guild

        Args:
            prefix: the prefix to add
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

        Args:
            prefix: the prefix to remove
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


def setup(bot):
    bot.add_cog(Server(bot))
