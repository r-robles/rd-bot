from discord.ext.commands import MemberConverter
from discord import utils


class InsensitiveMemberConverter(MemberConverter):
    async def convert(self, ctx, argument):
        try:
            return await super().convert(ctx, argument)
        except Exception as e:
            member_to_find = argument.lower()
            predicate = (lambda m: member_to_find in m.display_name.lower()
                         or member_to_find in m.name.lower())
            result = utils.find(predicate, ctx.guild.members)
            if result:
                return result
            raise e
