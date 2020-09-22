from abc import ABC
import asyncio
import logging
import math
from typing import List, Union
import discord
from discord.ext.commands import Context
from utils.messages import ColoredEmbed

# The max message size is actually 2000, but is left at 1900 to give some buffer room.
MAX_MESSAGE_SIZE = 1900

log = logging.getLogger(__name__)


class PaginationError(Exception):
    """Base error for pagination."""
    pass


class Paginator(ABC):
    LEFT_ARROW = '\u2b05'
    RIGHT_ARROW = '\u27a1'
    REACTION_EMOJIS = (LEFT_ARROW, RIGHT_ARROW)

    def __init__(self,
                 ctx: Context,
                 pages: Union[List[str], List[discord.Embed]],
                 current_page: int = 0,
                 timeout: int = 300,
                 *args,
                 **kwargs):
        """Create a Paginator object, which is used to allow the command invoker to change pages using reaction emojis.

        :param ctx: the Context object
        :param pages: the pages to display
        :param current_page: the starting page (when the initial message is sent)
        :param timeout: the maximum amount of time given to flip through pages
        :raises PaginationError: if there are no pages
        """
        if not pages:
            raise PaginationError('There are no pages.')

        self.ctx = ctx
        self.current_page = current_page
        self.timeout = timeout
        self.pages = pages

        self.message = None

    def _check_reaction(self, reaction: discord.Reaction, user: discord.Member):
        return (reaction.message.id == self.message.id
                and str(reaction.emoji) in self.REACTION_EMOJIS
                and user.id == self.ctx.author.id
                and not user.bot)

    async def send_message(self):
        """Send a message to a text channel and allow the command invoker to flip through pages using reaction emojis.
        """
        content_to_display = self.pages[self.current_page]

        if isinstance(content_to_display, str):
            self.message = await self.ctx.send(content_to_display)
        elif isinstance(content_to_display, discord.Embed):
            self.message = await self.ctx.send(embed=content_to_display)

        # If there's only one page, we don't need to add a reaction listener or page control emojis, so just exit.
        if not len(self.pages) > 1:
            return

        log.debug(f'Page length is {len(self.pages)}. Adding reaction emojis.')
        for emoji in self.REACTION_EMOJIS:
            await self.message.add_reaction(emoji)

        while True:
            try:
                reaction, user = await self.ctx.bot.wait_for('reaction_add',
                                                             timeout=self.timeout,
                                                             check=self._check_reaction)
            except asyncio.TimeoutError:
                break

            new_page = self.current_page
            if str(reaction.emoji) == self.LEFT_ARROW:
                log.debug('Left arrow emoji clicked. Attempting to move to the previous page.')
                new_page = max(0, self.current_page - 1)
            elif str(reaction.emoji) == self.RIGHT_ARROW:
                log.debug('Right arrow emoji clicked. Attempting to move to the next page.')
                new_page = min(len(self.pages) - 1, self.current_page + 1)

            if new_page != self.current_page:
                self.current_page = new_page
                content_to_display = self.pages[self.current_page]
                if isinstance(content_to_display, str):
                    await self.message.edit(content=content_to_display)
                elif isinstance(content_to_display, discord.Embed):
                    await self.message.edit(embed=content_to_display)


class CodeBlockPaginator(Paginator):
    CODE_BLOCK_PREFIX = '```\n'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def _finish_page(page_content, pages):
        page_content = '\n'.join((page_content,
                                  '```'))
        pages.append(page_content)

    @classmethod
    def paginate(cls, ctx: Context, content: str):
        """Paginate a list of items to display in an embed.

        The list of items passed will be set in the description field of an Embed object.

        :param ctx: the Context object
        :param content: the content to paginate
        :returns: a CodeBlockPaginator
        :raises PaginationError: if there is no content to paginate
        """
        if not content:
            raise PaginationError('There is nothing to paginate.')

        pages = []
        lines = content.splitlines()
        current_page_content = cls.CODE_BLOCK_PREFIX
        for line in lines:
            if (len(current_page_content) + len(line)) <= MAX_MESSAGE_SIZE:
                # Add the line to the current page.
                current_page_content = '\n'.join((current_page_content, line))
            else:
                # If it hits the maximum message size, finish the code block and add the new page. Reset the current
                # page content for the next iteration.
                log.debug('Maximum message size will be hit. Creating new page.')
                cls._finish_page(current_page_content, pages)
                current_page_content = cls.CODE_BLOCK_PREFIX
        # If there's still left over contents, finish the code block and add a new page.
        if current_page_content != cls.CODE_BLOCK_PREFIX:
            log.debug('There is still leftover page content. Creating new page.')
            cls._finish_page(current_page_content, pages)
        return cls(ctx=ctx,
                   pages=pages)


class EmbedListPaginator(Paginator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def _add_page_numbers(pages, total_items):
        for index, page in enumerate(pages):
            page.set_footer(text=f'Page {index + 1}/{len(pages)} ({total_items} total)')

    @staticmethod
    def _finish_page(page_content, current_page_embed, pages):
        current_page_embed.description = page_content
        pages.append(current_page_embed)

    @classmethod
    def paginate(cls,
                 ctx: Context,
                 items: List[str],
                 items_per_page: int = 20,
                 current_page: int = 0,
                 title: str = None):
        """Paginate a list of items to display in an embed.

        The list of items passed will be set in the description field of an Embed object.

        :param ctx: the Context object
        :param items: the items to paginate
        :param items_per_page: the number of items to place per page
        :param current_page: the starting page to display
        :param title: the desired title for the embed
        :returns an EmbedListPaginator
        :raises PaginationError: if there are no items to paginate, the items per page is invalid, or the starting page
             is invalid
        """
        if not items:
            raise PaginationError('There are no items to paginate.')
        if items_per_page <= 0:
            raise PaginationError('There must be at least 1 item per page.')
        total_pages = math.ceil(len(items) / items_per_page)
        if (current_page + 1) > total_pages:
            raise PaginationError(f'Current page: {current_page + 1} exceeds the total number of pages: '
                                  f'{total_pages}.')

        pages = []

        current_page_embed = ColoredEmbed(title=title)
        current_page_content = ''
        for index, item in enumerate(items):
            current_page_content += '\n' + item
            if (index + 1) % items_per_page == 0:
                cls._finish_page(current_page_content, current_page_embed, pages)
                current_page_content = ''
                current_page_embed = ColoredEmbed(title=title)
        if current_page_content:
            cls._finish_page(current_page_content, current_page_embed, pages)

        total_items = len(items)
        cls._add_page_numbers(pages, total_items)

        return cls(ctx=ctx,
                   pages=pages,
                   current_page=current_page)
