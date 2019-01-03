import discord
from discord.ext import commands

class Admin:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, limit:int=100):
        try:
            await ctx.channel.purge(limit=limit+1)
        except:
            await ctx.send("Could not delete messages")
        else:
            await ctx.send("Deleted "+str(limit)+" messages.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def cleanup(self, ctx, limit:int=25):
        def check(message):
            return message.content.startswith("food!") or message.author == self.bot.user
        try:
            deleted = await ctx.channel.purge(limit=limit+1, check=check)
        except:
            await ctx.send("Could not delete messages")
        else:
            await ctx.send("Deleted "+str(len(deleted))+" messages.")

def setup(bot):
    bot.add_cog(Admin(bot))