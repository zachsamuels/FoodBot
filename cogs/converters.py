import discord
from discord.ext import commands

class MemberURLConverter(commands.MemberConverter):

    async def convert(self, ctx, argument):
        try:
            member = await super().convert(ctx, argument)
        except commands.BadArgument:
            return argument
        else:
            return member
