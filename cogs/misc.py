from datetime import datetime
from discord.ext import commands
from utils.messages import ColoredEmbed, MessageUtils

class Misc:
    """Miscellaneous commands."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Pong!"""
        start = ctx.message.created_at.now()
        message = await ctx.send(content=':ping_pong: Pong!')
        end = datetime.now()
        delta = end - start
        time = delta.microseconds / 1000.0
        await message.edit(content=f':ping_pong: Pong! Time: {time} ms.')

    @commands.command()
    async def botinfo(self, ctx):
        """See some information about the bot."""
        bot_user = self.bot.user
        app = await self.bot.application_info()

        bot_name = f'{bot_user.name}#{bot_user.discriminator}'
        owner = f'{app.owner.name}#{app.owner.discriminator}'
        num_servers = str(len(self.bot.guilds))
        num_members = str(len(self.bot.users))
        cpu_usage = f'{self.bot.cpu_percentage:.2f}%'
        ram_usage = f'{self.bot.ram_usage:.2f} MiB ({self.bot.ram_percentage:.2f}%)'
        uptime = MessageUtils.convert_time_delta(datetime.utcnow(), self.bot.startup_time)

        embed = ColoredEmbed()
        embed.set_author(name=bot_name, icon_url=bot_user.avatar_url)
        embed.add_field(name='Owner', value=owner, inline=False)
        embed.add_field(name='Servers', value=num_servers, inline=False)
        embed.add_field(name='Members', value=num_members)
        embed.add_field(name='CPU Usage', value=cpu_usage, inline=False)
        embed.add_field(name='RAM Usage', value=ram_usage, inline=False)
        embed.add_field(name='Uptime', value=uptime, inline=False)

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Misc(bot))
