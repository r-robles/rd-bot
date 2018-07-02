import aiohttp

class RiotApi:
    def __init__(self, api_key):
        self.API_KEY = api_key
        self.BASE_URL = 'https://{}.api.riotgames.com/lol/{}'

    async def _request(self, platform, endpoint, **kwargs):
        url = self.BASE_URL.format(platform, endpoint)
        params = {k: v for k, v in kwargs.items() if v is not None}
        params['api_key'] = self.API_KEY
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as r:
                return await r.json()

    async def get_all_champions(self, platform, free_to_play=False):
        endpoint = 'platform/v3/champions'
        return await self._request(platform,
                                   endpoint,
                                   freeToPlay=str(free_to_play).lower()
        )

    async def get_champion_by_id(self, platform, champion_id):
        endpoint = 'platform/v3/champions/' + str(champion_id)
        return await self._request(platform,
                                   endpoint
        )

    async def get_league_by_summoner_id(self, platform, summoner_id):
        endpoint = 'league/v3/positions/by-summoner/' + str(summoner_id)
        return await self._request(platform,
                                   endpoint
        )

    async def get_lol_status(self, platform):
        endpoint = 'status/v3/shard-data'
        return await self._request(platform,
                                   endpoint
        )

class StaticApi:
    def __init__(self):
        self.BASE_URL = 'https://ddragon.leagueoflegends.com/cdn/{}/data/{}/{}'
        self.REALMS_URL = 'https://ddragon.leagueoflegends.com/realms/{}.json'

    async def _request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                return await r.json()

    async def get_champion_info(self, region):
        info = await self.get_realm_info(region)
        version = info['n']['champion']
        locale = info['l']
        url = self.BASE_URL.format(version, locale, 'champion.json')
        return await self._request(url)

    async def get_realm_info(self, region):
        region = region.lower()
        url = self.REALMS_URL.format(region)
        return await self._request(url)
