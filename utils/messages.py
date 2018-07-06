import discord

class ColoredEmbed(discord.Embed):
    def __init__(self, **kwargs):
        super().__init__(colour=0x3dbbe5, **kwargs)
