import traceback
import sys
from discord.ext import commands
import discord
import difflib
import json
from asyncpg import exceptions
import asyncio

class CommandErrorHandler:
    def __init__(self, bot):
        self.bot = bot

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

        elif isinstance(error, exceptions.NotNullViolationError):
            return await ctx.send(f"User is not in the system. Use {ctx.prefix}start")

        elif isinstance(error, asyncio.TimeoutError):
            return

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except:
                pass

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"You are missing an argument, use c!help {ctx.command} for more information!")

        elif isinstance(error, commands.BadArgument):
            return await ctx.send('I could not find that member. Please try again.')
        
        elif isinstance(error, commands.errors.MissingPermissions):
            if ctx.author == ctx.bot.owner:
                return await ctx.reinvoke()
            missing = "\n".join(error.missing_perms)
            return await ctx.send("You are missing the following permission/s, which is/are required to use this command:\n"+ missing)
        
        elif isinstance(error, commands.NotOwner):
            return await ctx.send("You must be the owner of this bot to use that command.")
            
        await ctx.message.add_reaction("\U0000274c")
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        tb=traceback.format_exception(type(error), error, error.__traceback__)
        msg=''
        for x in tb:
            msg= msg + x
        red = discord.Color.red()
        em = discord.Embed(title="Error",description=msg, color = red)
        await ctx.send(embed=em,delete_after=20)

def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
