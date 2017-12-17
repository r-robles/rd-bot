from datetime import datetime
import discord
from discord.ext import commands
from utils.riot_api import RiotApi, StaticApi

class League:
    def __init__(self, bot):
        self.bot = bot

        self.api = RiotApi(bot.config['riot_games'])
        self.static_api = StaticApi()

        self.regions = {
            'BR': 'br1',
            'EUNE': 'eun1',
            'EUW': 'euw1',
            'JP': 'jp1',
            'KR': 'kr',
            'LAN': 'la1',
            'LAS': 'la2',
            'NA': 'na1',
            'OCE': 'oc1',
            'TR': 'tr1',
            'RU': 'ru',
            'PBE': 'pbe1'
        }
        self.static_champ_data = None

    @commands.command()
    async def status(self, ctx, region='NA'):
        """Check if the League of Legends servers are up."""
        platform = self.regions[region.upper()]
        try:
            json = await self.api.get_status(platform)
        except KeyError:
            return await self.send_invalid_region(ctx)

        server = json['name']
        embed = discord.Embed(title=f'League of Legends Statuses for {server}',
                              timestamp=datetime.utcnow(),
                              colour=0x117711)
        for service in json['services']:
            name = service['name']
            if service['status'] == 'online':
                status = ':white_check_mark: Online'
            else:
                status = ':x: Offline'
            embed.add_field(name=name, value=status)
        await ctx.send(embed=embed)

    @commands.command()
    async def rotation(self, ctx, region='NA'):
        """List the champions on free rotation."""
        region = region.upper()
        platform = self.regions[region]
        try:
            json = await self.api.get_champions(platform, free_to_play=True)
        except KeyError:
            return await self.send_invalid_region(ctx)

        ids = [x['id'] for x in json['champions']]
        info = await self.static_api.get_champion_info(region)
        # Get all champion names that match the free champions
        names = [info['data'][c]['name'] for c in info['data'] for i in ids if str(i) == info['data'][c]['key']]

        embed = discord.Embed(timestamp=datetime.utcnow(), colour=0x117711)
        embed.add_field(name='League of Legends Free Champion Rotation',
                        value='\n'.join(names))
        await ctx.send(embed=embed)

    async def send_invalid_region(self, ctx):
        """Sends an embed stating an invalid region has been entered.
           Also gives a list of the valid regions that can be used.
        """
        text = ', '.join(self.regions.keys())
        return await ctx.send(f'Invalid region entered.\nValid regions: `{text}`')

def setup(bot):
    bot.add_cog(League(bot))
