import random
import discord
from discord.ext import commands
from utils.messages import ColoredEmbed


class Fun:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def xkcd(self, ctx):
        """See the latest XKCD comic.

        Usage:
            -xkcd
        """
        async with self.bot.session.get('https://xkcd.com/info.0.json') as r:
            if r.status == 200:
                json = await r.json()
                embed = ColoredEmbed(title=json['title'],
                                     description=json['alt'])
                embed.set_image(url=json['img'])
                await ctx.send(embed=embed)

    @commands.command()
    async def lenny(self, ctx):
        """( ͡° ͜ʖ ͡°)

        Usage:
            -lenny
        """
        await ctx.send('( ͡° ͜ʖ ͡°)')

    @commands.command(name='8ball')
    async def eight_ball(self, ctx, *, question):
        """Ask the magic 8 ball.

        Usage:
            -8ball [question]

        Args:
            question (str): the question to ask (must end with "?")
        """
        if not question.endswith('?'):
            await ctx.send('That\'s not a question!')
            return
        responses = ['It is certain.',
                     'It is decidedly so.',
                     'Without a doubt.',
                     'Yes - definitely.',
                     'You may rely on it.',
                     'As I see it, yes.',
                     'Most likely.',
                     'Outlook good.',
                     'Yes.',
                     'Signs point to yes.',
                     'Reply hazy, try again',
                     'Ask again later.',
                     'Better not tell you now.',
                     'Cannot predict now.',
                     'Concentrate and ask again.',
                     'Don\'t count on it.',
                     'My reply is no.',
                     'My sources say no.',
                     'Outlook not so good.',
                     'Very doubtful.']
        await ctx.send(f'You asked: **{question}**\n:8ball: {random.choice(responses)}')


def setup(bot):
    bot.add_cog(Fun(bot))
