import traceback
import sys
from discord.ext import commands
import discord
import difflib
import json
from asyncpg import exceptions
import asyncio

class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception"""
        
        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.UserInputError,commands.CommandNotFound)
        error = getattr(error, 'original', error)
        
        if isinstance(error,commands.CommandNotFound):
            return 
        elif isinstance(error, discord.Forbidden):
            return

        if isinstance(error, commands.CommandOnCooldown):
            time = round(error.retry_after/3600,1)
            return await ctx.send(f"You have to wait {time} hours to use this command")

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(f'{ctx.command} has been disabled.')

     
        elif isinstance(error, asyncio.TimeoutError):
            return

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except:
                pass

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"You are missing an argument, use food!help {ctx.command} for more information!")

        elif isinstance(error, commands.BadArgument):
            return await ctx.send('You passed an incorrect argument, use food!help for more help on how to use this command.')
        
        elif isinstance(error, commands.MissingPermissions):
            if ctx.author == ctx.bot.owner:
                return await ctx.reinvoke()
            missing = "\n".join(error.missing_perms)
            return await ctx.send("You are missing the following permission/s, which is/are required to use this command:\n"+ missing)
        
        elif isinstance(error, commands.NotOwner):
            return await ctx.send("You must be the owner of this bot to use that command.")
        
        elif isinstance(error, discord.NotFound):
            return

        await ctx.message.add_reaction("\U0000274c")
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        tb=traceback.format_exception(type(error), error, error.__traceback__)
        msg=''
        for x in tb:
            msg= msg + x
        capn = self.bot.get_user(422181415598161921)
        red = discord.Color.red()
        times = (len(msg) // 2000) + 1
        for i in range(times):
            first = i * 2000
            second = (i + 1) * 2000
            em = discord.Embed(title="Error", description=msg[first:second], color=red)
            if ctx.guild:
                g = str(ctx.guild.id)
            else:
                g = "No Guild"
            em.add_field(name="Info", value=str(ctx.author.id) + "\n" + g + "\n" + ctx.command.qualified_name)
            await capn.send(embed=em)
            await ctx.send("This command errored, The owner of the bot has been notified.")

def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
