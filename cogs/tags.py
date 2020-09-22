from datetime import datetime
from discord.ext import commands
from database.models.tag import Tag
from utils.paginator import EmbedListPaginator


class TagConverter(commands.clean_content):
    async def convert(self, ctx, tag):
        """
        Returns
        -------
        the tag in lowercase with leading and trailing whitespaces
        removed, or an empty string if no tag was entered to begin with
        """
        if not tag:
            return ''
        result = await super().convert(ctx, tag)
        result = result.strip().lower()
        return result


class Tags(commands.Cog):
    """Tag something for future reference."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, case_insensitive=True)
    async def tag(self, ctx, *, tag: TagConverter = None):
        """Search, create, edit, or remove a tag.

        If no command is specified, the tag will be searched for.
        """
        if tag is None:
            return await ctx.send_help(ctx.command)
        if ctx.invoked_subcommand is None:
            model = await Tag.get((ctx.guild.id, tag))

            if model:
                return await ctx.send(f'**{tag}**\n{model.content}')
            return await ctx.send('No tag exists with that name!')

    @tag.command(name='create')
    async def create_tag(self, ctx, tag: TagConverter = None, *, content=None):
        """Create a tag in this server.

        If the tag you want to create has more than one word, then it
        should be enclosed in double quotes.

        Tags can only be seen in the server they were created in.

        Args
        ----
        tag:
            the name of the tag to create
        content:
            the contents of the tag
        """
        if not tag:
            return await ctx.send('You must enter a tag to create!')
        if tag in ['create', 'delete', 'edit', 'list', 'owned']:
            return await ctx.send('You cannot create a tag with that name!')

        try:
            model = await Tag.create(guild_id=ctx.guild.id,
                                     name=tag,
                                     content=content,
                                     owner=ctx.author.id,
                                     last_modified=datetime.utcnow())
            return await ctx.send(f'The tag **{model.name}** has successfully been created!')
        except Exception:
            return await ctx.send('That tag already exists!')

    @tag.command(name='edit')
    async def edit_tag(self, ctx, tag: TagConverter = None, *, content):
        """Edit a tag you own.

        If your tag is more than one word, then it should be
        enclosed in double quotes.

        Args
        ----
        tag:
            the tag to edit
        content:
            the new content
        """
        model = await Tag.get((ctx.guild.id, tag))
        if model:
            if model.owner == ctx.author.id:
                await model.update(content=content, last_modified=datetime.utcnow()).apply()
                return await ctx.send('Your tag has been successfully edited.')
        return await ctx.send('Either there is no tag with that name or you do not own that tag.')

    @tag.command(name='delete')
    async def delete_tag(self, ctx, *, tag: TagConverter = None):
        """Delete a tag you own.

        Args
        ----
        tag:
            the tag to remove
        """
        model = await Tag.get((ctx.guild.id, tag))
        if model:
            if model.owner == ctx.author.id:
                await model.delete()
                return await ctx.send('Your tag has successfully been deleted.')
        return await ctx.send('Either there is no tag with that name or you do not own that tag.')

    def _format_tags_for_pagination(self, records):
        """Format the tags from the resulting database query into a
        string.

        :param records: the result from the database query
        :returns: a formatted string containing the list of tags from the database query
        """
        return [f'`{index + 1}.` {record[0]}' for index, record in enumerate(records)]

    @tag.command(name='list')
    async def list_tags(self, ctx):
        """List all tags that are saved in this server. """
        result = await Tag.select('name').where(Tag.guild_id == ctx.guild.id).gino.all()
        if result:
            tags = self._format_tags_for_pagination(result)
            title = f'Tags for {ctx.guild}'
            paginated_tags = EmbedListPaginator.paginate(ctx=ctx, items=tags, title=title)
            await paginated_tags.send_message()
        else:
            await ctx.send('No tags have been created in this server!')

    @tag.command(name='owned')
    async def list_owned_tags(self, ctx):
        """List all tags you own in this server."""
        result = await Tag.select('name').where(Tag.guild_id == ctx.guild.id) \
                                         .where(Tag.owner == ctx.author.id).gino.all()
        if result:
            tags = self._format_tags_for_pagination(result)
            title = f'Tags Owned by {ctx.author}'
            paginated_tags = EmbedListPaginator.paginate(ctx=ctx, items=tags, title=title)
            await paginated_tags.send_message()
        else:
            await ctx.send('You don\'t own any tags in this server!')


def setup(bot):
    bot.add_cog(Tags(bot))
