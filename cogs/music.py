from enum import Enum
import logging
import re
import lavalink
from discord.ext import commands
from lavalink import AudioTrack
from utils.messages import ColoredEmbed
from utils.paginator import EmbedListPaginator

url_rx = re.compile('https?:\/\/(?:www\.|(?!www))')

log = logging.getLogger(__name__)

class NoTrackPlayingError(commands.CommandInvokeError):
    pass


class NPEmbedSource(Enum):
    """Creation source of the 'now playing' embed. Used to determine
    the wording and information that should be displayed in the embed.
    """
    TRACK_START_EVENT = 1,
    NP_COMMAND = 2


class Track(AudioTrack):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def thumbnail(self):
        if self.uri.startswith('https://www.youtube.com'):
            return f'https://img.youtube.com/vi/{self.identifier}/mqdefault.jpg'
        return ''


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(bot.config['Lavalink']['host'],
                                  bot.config['Lavalink']['port'],
                                  bot.config['Lavalink']['password'],
                                  'na',
                                  'na-node')
            bot.add_listener(bot.lavalink.voice_update_handler, 'on_socket_response')
        lavalink.add_event_hook(self.handle_events)

    def cog_unload(self):
        """Clear all event hooks."""
        self.bot.lavalink._event_hooks.clear()

    async def cog_command_error(self, ctx, error):
        """Handler for exceptions raised in music commands."""
        if isinstance(error, commands.CommandInvokeError):
            log.warning(f'Exception occurred in music commands: {error}')
            await ctx.send(error.original)

    async def handle_events(self, event):
        # Disconnect from the voice channel if there's no music left in the queue.
        if isinstance(event, lavalink.QueueEndEvent):
            guild_id = event.player.guild_id
            await self._connect_to_voice_channel(guild_id, None)
        # Send a message showing the current track playing when a new track starts.
        elif isinstance(event, lavalink.TrackStartEvent):
            channel = self.bot.get_channel(event.player.fetch('channel'))
            embed = await self._create_np_embed(event.player,
                                                event.track,
                                                NPEmbedSource.TRACK_START_EVENT)
            await channel.send(embed=embed)

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
            duration = lavalink.format_time(track.duration)

        if source == NPEmbedSource.TRACK_START_EVENT:
            embed.add_field(name='Duration', value=duration)
        elif source == NPEmbedSource.NP_COMMAND:
            current_time = lavalink.format_time(player.position)
            embed.add_field(name='Current Time',
                            value=f'{current_time} / {duration}')

        embed.add_field(name='Volume', value=f'{player.volume}%')
        embed.set_footer(
            text=f'Repeat: {"on" if player.repeat else "off"}, Shuffle: {"on" if player.shuffle else "off"}')
        return embed

    async def _connect_to_voice_channel(self, guild_id: int, channel_id: str):
        """Connect to a voice channel in a guild. If channel_id is None, then the bot will disconnect from its voice
        channel."""
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)

    def _add_tracks_to_queue(self, player_manager, tracks, requester):
        added = []
        for t in tracks:
            track = Track(t, requester)
            player_manager.add(requester, track)
            added.append(track)
        return added

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
            query is specified, the first track in the queue will be played.
        """
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')

        # Attempt to play first track in the queue if no query is specified.
        if not query:
            if not player.queue:
                return await ctx.send('The queue is empty. Add something to play.')
            if not player.is_playing:
                return await player.play()
            return await ctx.send('I\'m already playing music in a voice channel.')

        # Links in messages are surrounded by angled brackets, so we strip these out.
        query = query.strip('<>')

        # Prefix query with 'ytsearch:' to default to YouTube searches only when the query
        # is a link, or when the user specifies a SoundCloud search.
        if not url_rx.match(query) and not query.startswith('scsearch:'):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)

        if not results:
            return await ctx.send('An error occurred while trying to find your song. Please try again later.')
        elif results['loadType'] == 'NO_MATCHES':
            return await ctx.send('No tracks have been found with that name.')
        elif results['loadType'] == 'PLAYLIST_LOADED':
            tracks_added = self._add_tracks_to_queue(player, results['tracks'], ctx.author.id)
            # Show added tracks from playlist
            formatted_tracks = self._format_tracks_for_pagination(tracks_added)
            title = f'Playlist {results["playlistInfo"]["name"]} Added to Queue'
            paginated_tracks = EmbedListPaginator.paginate(ctx=ctx, items=formatted_tracks, title=title,
                                                           items_per_page=15)
            # Prevent the pagination controller from blocking the play (at the end).
            self.bot.loop.create_task(paginated_tracks.send_message())
        elif results['loadType'] == 'SEARCH_RESULT' or results['loadType'] == 'TRACK_LOADED':
            # Load only the first track
            track_added, = self._add_tracks_to_queue(player, results['tracks'][:1], ctx.author.id)
            embed = ColoredEmbed(title=f'Track Added to Position {len(player.queue)} in Queue',
                                 description=f'[{track_added.title}]({track_added.uri})')
            embed.set_thumbnail(url=track_added.thumbnail)
            await ctx.send(embed=embed)
        else:
            return await ctx.send('I am unable to load this video. Try a different one instead.')

        if not player.is_playing:
            await player.play()

    @commands.guild_only()
    @commands.command()
    async def pause(self, ctx):
        """Pause the music player."""
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')

        if player.paused:
            return await ctx.send('Music player is already paused.')
        await player.set_pause(True)
        return await ctx.send('Music player has been paused.')

    @commands.guild_only()
    @commands.command()
    async def resume(self, ctx):
        """Resume the music player."""
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')

        if not player.paused:
            return await ctx.send('Music player has already resumed.')
        await player.set_pause(False)
        return await ctx.send('Music player has been resumed.')

    @commands.guild_only()
    @commands.command()
    async def skip(self, ctx):
        """Skip the current track."""
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')
        await player.skip()
        await ctx.message.add_reaction('✅')

    @commands.guild_only()
    @commands.command()
    async def stop(self, ctx):
        """Disconnect the player from the voice channel."""
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')
        await player.stop()
        await self._connect_to_voice_channel(ctx.guild.id, None)
        await ctx.message.add_reaction('✅')

    @commands.command()
    @commands.guild_only()
    async def remove(self, ctx, track: int):
        """Remove a track from the queue.

        Args
        ----
        track:
            the track number to remove from the queue
        """
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')

        if not player.queue:
            return await ctx.send('There are no tracks in the queue.')

        if not 0 < track <= len(player.queue):
            return await ctx.send(f'Track number must be **between** 1 and {len(player.queue)}')

        removed = player.queue.pop(track - 1)
        await ctx.send(f'Removed **{removed.title}** from the queue.')

    @commands.guild_only()
    @commands.command()
    async def repeat(self, ctx):
        """Toggle track repeat."""
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')

        player.repeat = not player.repeat
        await ctx.send(f'Repeat is now {"on" if player.repeat else "off"}.')

    @commands.command()
    @commands.guild_only()
    async def shuffle(self, ctx):
        """Toggle track shuffle."""
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')

        player.shuffle = not player.shuffle
        await ctx.send(f'Shuffle is now {"on" if player.shuffle else "off"}.')

    @commands.guild_only()
    @commands.command()
    async def clear(self, ctx):
        """Clear the queue."""
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')
        player.queue.clear()
        await ctx.send('The queue has been cleared.')

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
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')

        if volume is None:
            return await ctx.send(f'Volume is currently set to {player.volume}%.')
        elif not 0 <= volume <= 100:
            return await ctx.send(f'Volume must be between 0 and 100.')

        await player.set_volume(volume)
        await ctx.send(f'Volume has been set to {player.volume}%.')

    @commands.command(name='np')
    @commands.guild_only()
    async def show_current_track(self, ctx):
        """Show the track currently playing."""
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')

        embed = await self._create_np_embed(player, player.current, NPEmbedSource.NP_COMMAND)
        await ctx.send(embed=embed)

    @commands.command(name='playfrom', aliases=['pf'])
    @commands.guild_only()
    async def playfrom(self, ctx, track: int):
        """Play the queue from a specific track number.

        NOTE: All tracks before this will be discarded.

        Args
        ----
        track:
            the track number in the queue to start playing from
        """
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')

        if track < 1 or track > len(player.queue):
            return await ctx.send('This track number does not exist.')

        player.queue = player.queue[track - 1:]
        await player.play()

    @commands.command()
    @commands.guild_only()
    async def seek(self, ctx, *, time: int = None):
        """Seek forward or backwards in the track.

        Args
        ----
        time:
            the amount of seconds to move forward or backward in the
            track
        """
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')

        if not time:
            return await ctx.send('You need to specify the amount of seconds to seek.')

        track_time = player.position + (time * 1000)
        await player.seek(track_time)

        await ctx.send(f'Moved track to **{lavalink.format_time(track_time)}**')

    def _format_tracks_for_pagination(self, tracks):
        return [f'`{index + 1}.` [**{track.title}**]({track.uri})' for index, track in enumerate(tracks)]

    @commands.command(name='queue', aliases=['q'])
    @commands.guild_only()
    async def queue(self, ctx, page: int = 1):
        """Show the player's queue.

        Args
        ----
        page:
            the page number to show in the queue
        """
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')

        if not player.queue:
            return await ctx.send('No tracks are currently in the queue.')

        # Make page 0-indexed.
        current_page = page - 1

        queue = self._format_tracks_for_pagination(player.queue)
        title = f'Music Queue for {ctx.guild}'

        paginated_queue = EmbedListPaginator.paginate(ctx=ctx, items=queue, current_page=current_page, title=title,
                                                      items_per_page=15)
        await paginated_queue.send_message()

    @play.before_invoke
    @playfrom.before_invoke
    async def ensure_caller_in_voice_channel(self, ctx):
        """Ensure caller is in a voice channel and the bot has the correct permissions to join."""
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')

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
            await self._connect_to_voice_channel(ctx.guild.id, str(ctx.author.voice.channel.id))
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                return await ctx.send('I am already connected to a voice channel.')

    @pause.before_invoke
    @resume.before_invoke
    @seek.before_invoke
    @skip.before_invoke
    @show_current_track.before_invoke
    async def ensure_currently_playing(self, ctx):
        """Ensure the bot is currently playing some music before invoking certain commands."""
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, region='na')

        if not player.is_playing:
            raise NoTrackPlayingError('No track is being played right now.')


def setup(bot):
    bot.add_cog(Music(bot))
