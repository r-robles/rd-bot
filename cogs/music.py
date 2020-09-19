from enum import Enum
import logging
import math
import re
from utils.messages import ColoredEmbed
from discord.ext import commands
import lavalink


url_rx = re.compile('https?:\/\/(?:www\.)?.+')  # noqa: W605


class NoTrackPlayingError(commands.CommandInvokeError):
    pass


class NPEmbedSource(Enum):
    """Creation source of the 'now playing' embed. Used to determine
    the wording and information that should be displayed in the embed.
    """
    TRACK_START_EVENT = 1,
    NP_COMMAND = 2


class Music(commands.Cog):
    """Commands to play music in a voice channel."""

    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'lavalink'):
            self.bot.lavalink = self._initialize_client()
        self.bot.lavalink.register_hook(self.handle_events)

    def _initialize_client(self):
        config = self.bot.config['Lavalink']
        try:
            return lavalink.Client(bot=self.bot,
                            host=config['host'],
                            password=config['password'],
                            rest_port=config['port'],
                            ws_port=config['port'],
                            log_level=logging.INFO,
                            loop=self.bot.loop)
        except Exception as e:
            raise commands.ExtensionFailed('Failed to connect to Lavalink server.')

    def cog_unload(self):
        for guild_id, player in self.bot.lavalink.players:
            self.bot.loop.create_task(player.disconnect())
            player.cleanup()
        self.bot.lavalink.unregister_hook(self.handle_events)

    async def _create_np_embed(self, player, track, source):
        """Creates an embed showing the track currently playing.

        Args
        ----
        player:
            the music player for the guild
        track:
            the track currently playing
        source:
            where this function is being called from
        """
        embed = ColoredEmbed(title='Now Playing',
                             description=f'[{track.title}]({track.uri})')
        embed.set_thumbnail(url=track.thumbnail)

        requester = await self.bot.fetch_user(track.requester)
        embed.add_field(name='Requested by', value=f'{requester}')

        if track.stream:
            duration = '🔴 LIVE'
        else:
            duration = lavalink.Utils.format_time(track.duration)

        if source == NPEmbedSource.TRACK_START_EVENT:
            embed.add_field(name='Duration', value=duration)
        elif source == NPEmbedSource.NP_COMMAND:
            current_time = lavalink.Utils.format_time(player.position)
            embed.add_field(name='Current Time',
                            value=f'{current_time} / {duration}')

        embed.add_field(name='Volume', value=f'{player.volume}%')
        embed.set_footer(
            text=f'Repeat: {"on" if player.repeat else "off"}, Shuffle: {"on" if player.shuffle else "off"}')

        return embed

    async def handle_events(self, event):
        """Handlers for Lavalink events."""
        if isinstance(event, lavalink.Events.TrackStartEvent):
            channel = self.bot.get_channel(event.player.fetch('channel'))

            embed = await self._create_np_embed(event.player, event.track, NPEmbedSource.TRACK_START_EVENT)
            await channel.send(embed=embed)
        elif isinstance(event, lavalink.Events.QueueEndEvent):
            await event.player.disconnect()

    async def cog_command_error(self, ctx, error):
        """Handler for exceptions raised in music commands."""
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)

    @commands.guild_only()
    @commands.command()
    async def play(self, ctx, *, query: str = None):
        """Play the track or playlist you want.

        If the bot is already playing something, then the track/playlist
        will be added to the end of the queue.

        Args
        ----
        query:
            the url or query of the track/song you want to play. If no
            query is specified, the first track in the queue is played.
        """
        player = self.bot.lavalink.players.get(ctx.guild.id)

        # Play first track in the queue if no query is specified
        if query is None:
            if not player.queue:
                return await ctx.send('The queue is empty. Add something to play!')

            if not player.is_playing:
                play_at_command = self.bot.get_command('playfrom')
                return await ctx.invoke(play_at_command, 1)
            else:
                return await ctx.send('I\'m already playing music in your channel!')

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

            embed = ColoredEmbed(title='Playlist Added to Queue',
                                 description=f'{len(tracks)} tracks from [{results["playlistInfo"]["name"]}]({query}) have been added to your queue.')
            await ctx.send(embed=embed)
        elif results['loadType'] == 'SEARCH_RESULT' or results['loadType'] == 'TRACK_LOADED':
            track = results['tracks'][0]
            player.add(requester=ctx.author.id, track=track)
            embed = ColoredEmbed(title=f'Track Added to Position {len(player.queue)} in Queue',
                                 description=f'[{track["info"]["title"]}]({track["info"]["uri"]})')
            await ctx.send(embed=embed)
        else:
            return await ctx.send('I am unable to load this video. Try a different one instead.')

        if not player.is_playing:
            await player.play()

    @commands.command(name='playfrom', aliases=['pf'])
    @commands.guild_only()
    async def playfrom(self, ctx, track: int):
        """Play the queue from a specific track number.

        All tracks before this will be discarded.

        Args
        ----
        track:
            the track number in the queue to start playing from
        """
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if track < 1 or track > len(player.queue):
            return await ctx.send('This track number does not exist.')

        await player.play_at(track-1)

    @commands.command()
    @commands.guild_only()
    async def seek(self, ctx, *, time: int = None):
        """Seek to a given position in a track.

        Args
        ----
        time:
            the amount of seconds to move forward or backward in the
            track
        """
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not time:
            return await ctx.send('You need to specify the amount of seconds to skip.')

        track_time = player.position + (time * 1000)
        await player.seek(track_time)

        await ctx.send(f'Moved track to **{lavalink.Utils.format_time(track_time)}**')

    @commands.guild_only()
    @commands.command()
    async def previous(self, ctx):
        """Play the previous track."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        try:
            await player.play_previous()
            await ctx.message.add_reaction('✅')
        except lavalink.NoPreviousTrack:
            await ctx.send('No track was previously played.')

    @commands.guild_only()
    @commands.command()
    async def skip(self, ctx):
        """Skip the current track."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        await player.skip()
        await ctx.message.add_reaction('✅')

    @commands.command(name='disconnect', aliases=['dc', 'stop'])
    @commands.guild_only()
    async def disconnect(self, ctx):
        """Disconnect the player from the voice channel."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        await player.disconnect()
        await ctx.message.add_reaction('✅')

    @commands.command(name='np')
    @commands.guild_only()
    async def now_playing(self, ctx):
        """Show the track currently playing."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        embed = await self._create_np_embed(
            player, player.current, NPEmbedSource.NP_COMMAND)
        await ctx.send(embed=embed)

    @commands.command(name='queue', aliases=['q'])
    @commands.guild_only()
    async def queue(self, ctx, page: int = 1):
        """Show the player's queue.

        Args
        ----
        page:
            the page number to show in the queue
        """
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.queue:
            return await ctx.send('No tracks are currently in the queue.')

        items_per_page = 10
        pages = math.ceil(len(player.queue) / items_per_page)

        if page > pages:
            return await ctx.send(f'Page {page} does not exist in this queue.')

        start = (page - 1) * items_per_page
        end = min(start + items_per_page, len(player.queue))

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
        """Pause/resume the current track."""
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
        """Change the player's volume.

        Args
        ----
        volume:
            the new volume to be set. If volume is not specified, the
            current volume will be shown.
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
        """Toggle track shuffle."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        player.shuffle = not player.shuffle
        await ctx.send(f'Shuffle is now {"on" if player.shuffle else "off"}.')

    @commands.command()
    @commands.guild_only()
    async def repeat(self, ctx):
        """Toggle track repeat."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        player.repeat = not player.repeat
        await ctx.send(f'Repeat is now {"on" if player.repeat else "off"}.')

    @commands.command(name='remove')
    @commands.guild_only()
    async def remove(self, ctx, track: int):
        """Remove a track from the queue.

        Args
        ----
        track:
            the track number to remove from the queue
        """
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.queue:
            return await ctx.send('There are no tracks in the queue.')

        if not 0 < track <= len(player.queue):
            return await ctx.send(f'Track number must be **between** 1 and {len(player.queue)}')

        removed = player.queue.pop(track - 1)

        await ctx.send(f'Removed **{removed.title}** from the queue.')

    @commands.command()
    @commands.guild_only()
    async def clear(self, ctx):
        """Clear the queue."""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        player.queue.clear()
        await ctx.send('The queue has been cleared.')

    @play.before_invoke
    @previous.before_invoke
    @playfrom.before_invoke
    async def ensure_voice(self, ctx):
        """A few checks to make sure the bot can join a voice channel."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.is_connected:
            if not ctx.author.voice or not ctx.author.voice.channel:
                raise commands.CommandInvokeError(
                    'You aren\'t connected to any voice channel.')

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect:
                raise commands.CommandInvokeError(
                    'I am missing `CONNECT` permissions in your voice channel.')
            if not permissions.speak:
                raise commands.CommandInvokeError(
                    'I am missing `SPEAK` permissions in your voice channel.')

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
        """Ensure the bot is currently playing some music before
        invoking certain commands."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.is_playing:
            raise NoTrackPlayingError('No track is being played right now.')


def setup(bot):
    bot.add_cog(Music(bot))
