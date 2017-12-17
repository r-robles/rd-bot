import aiohttp

class RiotApi:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://{}.api.riotgames.com{}'

    async def _request(self, platform, endpoint, **kwargs):
        url = self.base_url.format(platform, endpoint)
        params = {k: v for k, v in kwargs.items() if v is not None}
        params['api_key'] = self.api_key
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as r:
                return await r.json()

    async def get_status(self, platform):
        endpoint = '/lol/status/v3/shard-data'
        return await self._request(platform, endpoint)

    async def get_champions(self, platform, free_to_play=False):
        endpoint= '/lol/platform/v3/champions'
        return await self._request(platform,
                                   endpoint,
                                   freeToPlay=str(free_to_play).lower()
        )

    async def get_champions_from_static_data(self, platform, data_by_id=False):
        endpoint = '/lol/static-data/v3/champions'
        return await self._request(platform,
                                   endpoint,
                                   dataById=str(data_by_id).lower()
        )

class StaticApi:
    def __init__(self):
        self.base_url = 'https://ddragon.leagueoflegends.com/cdn/{}/data/{}/{}'
        self.realms_url = 'https://ddragon.leagueoflegends.com/realms/{}.json'

    async def _request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                return await r.json()

    async def get_champion_info(self, region):
        info = await self.get_realm_info(region)
        version = info['n']['champion']
        locale = info['l']
        url = self.base_url.format(version, locale, 'champion.json')
        return await self._request(url)

    async def get_realm_info(self, region):
        region = region.lower()
        url = 'https://ddragon.leagueoflegends.com/realms/{}.json'.format(region)
        return await self._request(url)
