import discord
from discord.ext import commands


class Tag:
    """Tag something for future reference."""

    def __init__(self, bot):
        self.bot = bot

    async def search_tag(self, tag):
        query = 'select * from tags where name = $1;'

        return await self.bot.database.fetchrow(query, tag)

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx, *, tag=None):
        """Search, create, edit, or remove a tag.

        If no command is specified, the tag will be searched.
        """
        if tag is None:
            help_command = self.bot.get_command('help')
            return await ctx.invoke(help_command, 'tag')
        if ctx.invoked_subcommand is None:
            result = await self.search_tag(tag)

            if result:
                content = result['content']
                await ctx.send(f'**{tag}**\n{content}')
            else:
                await ctx.send('No tag exists with that name!')

    @tag.command(name='create')
    async def create_tag(self, ctx, tag, *, content=None):
        """Create a tag.

        If the tag you want to create has more than one word, then it
        should be enclosed in double quotes.

        Args:
            tag: the name of the tag to create
            content (optional): the contents of the tag
        """
        result = await self.search_tag(tag)

        if result is None:
            owner_id = ctx.author.id

            query = 'insert into tags(name, owner, content) values($1, $2, $3);'
            await self.bot.database.execute(query, tag, owner_id, content)

            await ctx.send(f'The tag **{tag}** has successfully been created!')
        else:
            await ctx.send('That tag already exists!')

    @tag.command(name='edit')
    async def edit_tag(self, ctx, tag, *, content):
        """Edit a tag you own.

        If your tag is more than one word, then it should be
        enclosed in double quotes.

        Args:
            tag: the tag to edit
            content: the new content
        """
        result = await self.search_tag(tag)

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
    async def remove_tag(self, ctx, *, tag):
        """Remove a tag you own.

        Args:
            tag: the tag to remove
        """
        result = await self.search_tag(tag)

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


def setup(bot):
    bot.add_cog(Tag(bot))
