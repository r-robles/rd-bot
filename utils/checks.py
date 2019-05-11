from discord.ext import commands


def has_guild_permissions(**perms):
    """Check to see if a member has matching permissions in the
    guild."""
    def predicate(ctx):
        user = ctx.author
        guild_perms = user.guild_permissions

        missing = [perm for perm, val in perms.items()
                   if getattr(guild_perms, perm) != val]

        if not missing:
            return True
        raise commands.MissingPermissions(missing)
    return commands.check(predicate)
