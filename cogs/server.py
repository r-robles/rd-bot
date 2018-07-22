import discord
from discord.ext import commands
from utils.converters import InsensitiveMemberConverter
from utils.messages import ColoredEmbed


class Server:
    """Server related commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def serverinfo(self, ctx):
        """Get information about the server."""
        guild = ctx.guild
        embed = ColoredEmbed(title=guild.name)
        embed.add_field(name='ID', value=guild.id)
        embed.add_field(
            name='Owner', value=f'{guild.owner.name}#{guild.owner.discriminator}')
        embed.add_field(name='Server Region', value=guild.region)
        embed.add_field(name='Members', value=guild.member_count)
        embed.add_field(name='Text Channels',
                        value=f'{len(guild.text_channels)}')
        embed.add_field(name='Voice Channels',
                        value=f'{len(guild.voice_channels)}')
        roles = [role.name for role in guild.roles if role.name != '@everyone']
        embed.add_field(name='Roles', value=', '.join(roles), inline=False)
        create_time = guild.created_at.strftime('%B %d, %Y at %H:%M:%S UTC')
        embed.set_footer(text=f'Created on {create_time}')
        embed.set_thumbnail(url=guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def avatar(self, ctx, *, member: InsensitiveMemberConverter):
        """Get someone's avatar."""
        avatar = member.avatar_url_as(static_format='png')
        embed = ColoredEmbed()
        embed.set_author(name=member, icon_url=avatar)
        embed.set_image(url=avatar)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Server(bot))
