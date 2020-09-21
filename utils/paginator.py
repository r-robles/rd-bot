from abc import ABC
import asyncio
import logging
import discord
from discord.ext.commands import Context

MAX_MESSAGE_SIZE = 1900
log = logging.getLogger(__name__)


class Paginator(ABC):
    LEFT_ARROW = '\u2b05'
    RIGHT_ARROW = '\u27a1'
    REACTION_EMOJIS = (LEFT_ARROW, RIGHT_ARROW)

    def __init__(self,
                 ctx=None,
                 content=None,
                 current_page=0,
                 timeout=300,
                 pages=[],
                 *args,
                 **kwargs):
        self.ctx = ctx
        self.content = content
        self.current_page = current_page
        self.timeout = timeout
        self.pages = pages
        self.message = None

    async def send_message(self):
        content_to_display = self.pages[self.current_page]

        if isinstance(content_to_display, str):
            self.message = await self.ctx.send(content_to_display)
        elif isinstance(content_to_display, discord.Embed):
            self.message = await self.ctx.send(embed=content_to_display)

        # Only add arrow reactions if there is more than 1 page in the content
        log.info(self.pages)
        if len(self.pages) > 1:
            log.info(f'Page length is {len(self.pages)}. Adding reaction emojis.')
            for emoji in self.REACTION_EMOJIS:
                await self.message.add_reaction(emoji)

        def check_reaction(r: discord.Reaction, u: discord.Member):
            log.info(f'Reaction: {r}')
            log.info(f'User: {u}')
            return (r.message.id == self.message.id
                    and str(r.emoji) in self.REACTION_EMOJIS
                    and u.id == self.ctx.author.id
                    and not u.bot)

        while True:
            try:
                reaction, user = await self.ctx.bot.wait_for('reaction_add',
                                                             timeout=self.timeout,
                                                             check=check_reaction)
            except asyncio.TimeoutError:
                break

            new_page = self.current_page
            if str(reaction.emoji) == self.LEFT_ARROW:
                log.info('Left arrow emoji clicked. Attempting to move to the previous page.')
                new_page = max(0, self.current_page - 1)
            elif str(reaction.emoji) == self.RIGHT_ARROW:
                log.info('Right arrow emoji clicked. Attempting to move to the next page.')
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
            log.debug(f'There is still leftover page content. Creating new page.')
            cls._finish_page(current_page_content, pages)
        return cls(ctx=ctx,
                   pages=pages)
