import datetime
import discord


class MessageUtils:

    @staticmethod
    def convert_time_delta(end: datetime, start: datetime):
        delta = end - start
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        days_text = 'days' if days != 1 else 'day'
        hours_text = 'hours' if hours != 1 else 'hour'
        minutes_text = 'minutes' if minutes != 1 else 'minute'
        seconds_text = 'seconds' if seconds != 1 else 'second'

        if days > 0:
            return f'{days} {days_text}, {hours} {hours_text}, {minutes} {minutes_text}, {seconds} {seconds_text}'
        if hours > 0:
            return f'{hours} {hours_text}, {minutes} {minutes_text}, {seconds} {seconds_text}'
        if minutes > 0:
            return f'{minutes} {minutes_text}, {seconds} {seconds_text}'
        return f'{seconds} {seconds_text}'

    @staticmethod
    def convert_time(time: datetime):
        return time.strftime('%B %d, %Y at %H:%M:%S UTC')


class ColoredEmbed(discord.Embed):
    def __init__(self, **kwargs):
        super().__init__(colour=0x3dbbe5, **kwargs)
