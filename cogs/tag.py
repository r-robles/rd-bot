import discord
from discord.ext import commands
from utils.messages import ColoredEmbed


class TagConverter(commands.clean_content):
    async def convert(self, _, tag):
        """
        Returns:
            the tag in all lowercase characters, and with leading and
            trailing whitespaces removed. If the resulting tag is
            empty, then None is returned
        """
        result = tag.strip(' ').lower()
        return result if len(result) > 0 else None


class Tag:
    """Tag something for future reference."""

    def __init__(self, bot):
        self.bot = bot

    async def search_tag(self, tag, guild_id):
        query = 'select * from tags where name = $1 and guild_id = $2;'
        return await self.bot.database.fetchrow(query, tag, guild_id)

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx, *, tag: TagConverter = None):
        """Search, create, edit, or remove a tag.

        If no command is specified, the tag will be searched for.
        """
        if tag is None:
            help_command = self.bot.get_command('help')
            return await ctx.invoke(help_command, 'tag')
        if ctx.invoked_subcommand is None:
            result = await self.search_tag(tag, ctx.guild.id)

            if result:
                content = result['content']
                await ctx.send(f'**{tag}**\n{content}')
            else:
                await ctx.send('No tag exists with that name!')

    @tag.command(name='create')
    async def create_tag(self, ctx, tag: TagConverter = None, *, content=None):
        """Create a tag in this server.

        If the tag you want to create has more than one word, then it
        should be enclosed in double quotes.

        Tags can only be seen in the server they were created in.

        Args:
            tag: the name of the tag to create
            content (optional): the contents of the tag
        """
        guild_id = ctx.guild.id
        result = await self.search_tag(tag, guild_id)

        if result is None:
            query = 'insert into tags(name, owner, guild_id, content) values($1, $2, $3, $4);'
            await self.bot.database.execute(query, tag, ctx.author.id, guild_id, content)

            await ctx.send(f'The tag **{tag}** has successfully been created!')
        else:
            await ctx.send('That tag already exists!')

    @tag.command(name='edit')
    async def edit_tag(self, ctx, tag: TagConverter = None, *, content):
        """Edit a tag you own.

        If your tag is more than one word, then it should be
        enclosed in double quotes.

        Args:
            tag: the tag to edit
            content: the new content
        """
        result = await self.search_tag(tag, ctx.guild.id)

        if result:
            owner_id = ctx.author.id

            if result['owner'] == owner_id:
                tag_id = result['id']

                query = "update tags set content = $1 where id = $2;"
                await self.bot.database.execute(query, content, tag_id)

                await ctx.send('Your tag has been successfully edited!')
            else:
                await ctx.send('You cannot edit a tag that you do not own!')
        else:
            await ctx.send('There is no tag with that name!')

    @tag.command(name='remove', aliases=['delete'])
    async def remove_tag(self, ctx, *, tag: TagConverter = None):
        """Remove a tag you own.

        Args:
            tag: the tag to remove
        """
        result = await self.search_tag(tag, ctx.guild.id)

        if result:
            owner_id = ctx.author.id

            if result['owner'] == owner_id:
                tag_id = result['id']

                query = "delete from tags where id = $1;"
                await self.bot.database.execute(query, tag_id)

                await ctx.send('Your tag has been successfully removed!')
            else:
                await ctx.send('You remove a tag that you do not own!')
        else:
            await ctx.send('There is no tag with that name!')

    def bulletize_tags(self, record_result):
        """Format the tags from the resulting database query into a
        string.

        Args:
            record_result: the result from the database query

        Returns:
            a string containing the list of tags that start with
            bullet points and are separated by new lines
        """
        bulletized = ''
        for record in record_result:
            bulletized += f'**∙** {record["name"]}\n'
        return bulletized

    @tag.command(name='list')
    async def list_tags(self, ctx):
        """List all tags that are saved in this server.
        """
        query = "select name from tags where guild_id = $1 order by name;"
        result = await self.bot.database.fetch(query, ctx.guild.id)

        if result:
            tags = self.bulletize_tags(result)

            embed = ColoredEmbed()
            embed.add_field(name='Tags List', value=tags)
            await ctx.send(embed=embed)
        else:
            await ctx.send('No tags have been created in this server!')

    @tag.command(name='owned')
    async def owned_tags(self, ctx):
        """List all tags you own in this server.
        """
        query = "select name from tags where owner = $1 and guild_id = $2 order by name;"
        result = await self.bot.database.fetch(query, ctx.author.id, ctx.guild.id)

        if result:
            tags = self.bulletize_tags(result)

            embed = ColoredEmbed()
            embed.add_field(name=f'Tags Owned by {ctx.author}', value=tags)
            await ctx.send(embed=embed)
        else:
            await ctx.send('You don\'t own any tags in this server!')


def setup(bot):
    bot.add_cog(Tag(bot))
