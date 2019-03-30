import logging
import math
import re
import discord
from utils.messages import ColoredEmbed
from discord.ext import commands
import lavalink
from lavalink.PlayerManager import DefaultPlayer

url_rx = re.compile('https?:\/\/(?:www\.)?.+')  # noqa: W605


class NoTrackPlayingError(commands.CommandInvokeError):
    pass


class CustomPlayer(DefaultPlayer):
    """Lavalink player with default volume set to 50%."""

    def __init__(self, lavalink, guild_id: int):
        super().__init__(lavalink, guild_id)
        self.volume = 50


class Music(commands.Cog):
    """Commands to play music in a voice channel."""

    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'lavalink'):
            self.bot.lavalink = lavalink.Client(bot=bot,
                                                host=self.bot.config['Lavalink']['host'],
                                                password=self.bot.config['Lavalink']['password'],
                                                rest_port=self.bot.config['Lavalink']['port'],
                                                ws_port=self.bot.config['Lavalink']['port'],
                                                log_level=logging.DEBUG,
                                                loop=bot.loop,
                                                player=CustomPlayer)
        self.bot.lavalink.register_hook(self.handle_events)

    def cog_unload(self):
        for guild_id, player in self.bot.lavalink.players:
            self.bot.loop.create_task(player.disconnect())
            player.cleanup()
        self.bot.lavalink.unregister_hook(self.handle_events)

    async def handle_events(self, event):
        """Event handler for when tracks start and when the queue is clear."""
        if isinstance(event, lavalink.Events.TrackStartEvent):
            channel = self.bot.get_channel(event.player.fetch('channel'))
            embed = ColoredEmbed(title='Now Playing',
                                 description=f'[{event.track.title}]({event.track.uri})')
            embed.set_thumbnail(url=event.track.thumbnail)

            requester = await self.bot.fetch_user(event.track.requester)
            embed.add_field(name='Requested by', value=f'{requester}')

            if event.track.stream:
                duration = '🔴 LIVE'
            else:
                duration = lavalink.Utils.format_time(event.track.duration)
            embed.add_field(name='Duration', value=f'{duration}')
            await channel.send(embed=embed)
        elif isinstance(event, lavalink.Events.QueueEndEvent):
            await event.player.disconnect()

    @commands.guild_only()
    @commands.command()
    async def play(self, ctx, *, query: str = None):
        """Plays a track you want.

        Args:
            query: the url or query of the track/song you want to play
                If no query is specified, the first track in the queue is played."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        # Play first track in the queue if no query specified
        if query is None:
            if not player.queue:
                return await ctx.send('Add a track to the queue first.')
            if not player.is_playing:
                play_at_command = self.bot.get_command('playat')
                return await ctx.invoke(play_at_command, 1)
            else:
                return await ctx.send('Enter a track or song to play first.')

        query = query.strip('<>')

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results = await self.bot.lavalink.get_tracks(query)

        if results['loadType'] == 'NO_MATCHES':
            return await ctx.send('No tracks have been found with that name.')
        elif results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']
            for track in tracks:
                player.add(requester=ctx.author.id, track=track)

            embed = ColoredEmbed(title=f'{results["playlistInfo"]["name"]} Playlist Added to Queue',
                                 description=f'{len(tracks)} tracks have been added to your queue.',
                                 url=query)
            await ctx.send(embed=embed)
        elif results['loadType'] == 'SEARCH_RESULT' or results['loadType'] == 'TRACK_LOADED':
            track = results['tracks'][0]
            player.add(requester=ctx.author.id, track=track)
            embed = ColoredEmbed(title='Track Added to Queue',
                                 description=f'[{track["info"]["title"]}]({track["info"]["uri"]})')
            await ctx.send(embed=embed)

        if not player.is_playing:
            await player.play()

    @commands.command(name='playat', aliases=['pa'])
    @commands.guild_only()
    async def playat(self, ctx, index: int):
        """Plays the queue from a specific point. Disregards tracks before the index.

        Args:
            index: the track number to start playing from in the queue
        """
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if index < 1:
            return await ctx.send('Invalid specified index.')

        if len(player.queue) < index:
            return await ctx.send('This index exceeds the queue\'s length.')

        await player.play_at(index-1)

    @commands.command()
    @commands.guild_only()
    async def seek(self, ctx, *, time: int = None):
        """Seeks to a given position in a track.

        Args:
            time: the amount of seconds to move forward in the track
        """
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not time:
            return await ctx.send('You need to specify the amount of seconds to skip!')

        track_time = player.position + (time * 1000)
        await player.seek(track_time)

        await ctx.send(f'Moved track to **{lavalink.Utils.format_time(track_time)}**')

    @commands.guild_only()
    @commands.command()
    async def previous(self, ctx):
        """Plays the previous track."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        try:
            await player.play_previous()
            await ctx.message.add_reaction('✅')
        except lavalink.NoPreviousTrack:
            await ctx.send('No track was previously played.')

    @commands.guild_only()
    @commands.command()
    async def skip(self, ctx):
        """Skips the current track."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        await player.skip()
        await ctx.message.add_reaction('✅')

    @commands.command(name='disconnect', aliases=['dc', 'stop'])
    @commands.guild_only()
    async def disconnect(self, ctx):
        """Disconnects the player from the voice channel."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        await player.disconnect()
        await ctx.message.add_reaction('✅')

    @commands.command(name='np')
    @commands.guild_only()
    async def now_playing(self, ctx):
        """Shows the track currently playing."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if player.current.stream:
            current_time = '🔴 LIVE'
        else:
            position = lavalink.Utils.format_time(player.position)
            duration = lavalink.Utils.format_time(player.current.duration)
            current_time = f'{position} / {duration}'
        requester = await self.bot.fetch_user(player.current.requester)

        embed = ColoredEmbed(title='Now Playing',
                             description=f'[{player.current.title}]({player.current.uri})')

        embed.add_field(name='Requested by', value=requester)
        embed.add_field(name='Current Time', value=current_time)
        embed.set_thumbnail(url=player.current.thumbnail)

        await ctx.send(embed=embed)

    @commands.command(name='queue', aliases=['q'])
    @commands.guild_only()
    async def queue(self, ctx, page: int = 1):
        """ Shows the player's queue.

        Args:
            page: the page number to show in the queue
        """
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.queue:
            return await ctx.send('No tracks are currently in the queue.')

        items_per_page = 10
        pages = math.ceil(len(player.queue) / items_per_page)

        if page > pages:
            return await ctx.send(f'Page {page} does not exist in this queue.')

        start = (page - 1) * items_per_page
        end = start + items_per_page

        current_page_queue = player.queue[start:end]

        queue_list = ''
        for index, track in enumerate(current_page_queue, start=start):
            queue_list += f'`{index + 1}.` [**{track.title}**]({track.uri})\n'

        embed = ColoredEmbed(title=f'Tracks {start + 1} to {end}',
                             description=f'{queue_list}')
        embed.set_footer(text=f'Page {page}/{pages}')
        await ctx.send(embed=embed)

    @commands.command(name='pause', aliases=['resume'])
    @commands.guild_only()
    async def pause_resume(self, ctx):
        """Pauses/Resume the current track."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if player.paused:
            await player.set_pause(False)
            await ctx.send('Player has been resumed.')
        else:
            await player.set_pause(True)
            await ctx.send('Player has been paused.')

    @commands.command(name='volume', aliases=['vol'])
    @commands.guild_only()
    async def volume(self, ctx, volume: int = None):
        """Changes the player's volume.

        Args:
            volume: the new volume to be set
                If volume is not specified, the current volume will be shown.
        """
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if volume is None:
            return await ctx.send(f'Volume is currently set to {player.volume}%.')
        elif not 0 <= volume <= 100:
            return await ctx.send(f'Volume must be between 0 and 100.')

        await player.set_volume(volume)
        await ctx.send(f'Volume has been set to {player.volume}%.')

    @commands.command()
    @commands.guild_only()
    async def shuffle(self, ctx):
        """Toggles track shuffle."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        player.shuffle = not player.shuffle
        await ctx.send(f'Shuffle is now {"enabled" if player.shuffle else "disabled"}.')

    @commands.command()
    @commands.guild_only()
    async def repeat(self, ctx):
        """Toggles track repeat."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        player.repeat = not player.repeat
        await ctx.send(f'Repeat is now {"enabled" if player.repeat else "disabled"}.')

    @commands.command(name='remove')
    @commands.guild_only()
    async def remove(self, ctx, index: int):
        """Removes an item from the player's queue with the given index.

        Args:
            index: the track to remove from the queue
        """
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.queue:
            return await ctx.send('There are no tracks in the queue.')

        if not 0 < index <= len(player.queue):
            return await ctx.send(f'Index has to be **between** 1 and {len(player.queue)}')

        removed = player.queue.pop(index - 1)

        await ctx.send(f'Removed **{removed.title}** from the queue.')

    @commands.command()
    @commands.guild_only()
    async def clear(self, ctx):
        """Clears the queue."""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        player.queue.clear()
        await ctx.send('Queue has been cleared.')

    @play.before_invoke
    @previous.before_invoke
    @playat.before_invoke
    async def ensure_voice(self, ctx):
        """A few checks to make sure the bot can join a voice channel."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.is_connected:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send('You aren\'t connected to any voice channel.')
                raise commands.CommandInvokeError(
                    'Invoker is not connected to a voice channel.')

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect:
                await ctx.send('I am missing `CONNECT` permissions in your voice channel.')
                raise commands.CommandInvokeError(
                    'Bot is missing CONNECT permissions.')
            if not permissions.speak:
                await ctx.send('I am missing `SPEAK` permissions in your voice channel.')
                raise commands.CommandInvokeError(
                    'Bot is missing SPEAK permissions.')

            player.store('channel', ctx.channel.id)
            await player.connect(ctx.author.voice.channel.id)
        else:
            if player.connected_channel.id != ctx.author.voice.channel.id:
                return await ctx.send('Join my voice channel!')

    @pause_resume.before_invoke
    @seek.before_invoke
    @skip.before_invoke
    @now_playing.before_invoke
    async def ensure_currently_playing(self, ctx):
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.is_playing:
            await ctx.send('No track is being played right now.')
            raise NoTrackPlayingError


def setup(bot):
    bot.add_cog(Music(bot))
