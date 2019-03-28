import discord
from discord.ext import commands
import os
import time
import psutil
import inspect
import git 
from .paginator import Pages, PaginatedHelpCommand, CannotPaginate

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process()
        bot.help_command = PaginatedHelpCommand()
        bot.help_command.cog = self

    def get_uptime(self, *, brief=False):
        now = time.time()
        delta = now - self.bot.launch_time
        (hours, remainder) = divmod(int(delta), 3600)
        (minutes, seconds) = divmod(remainder, 60)
        (days, hours) = divmod(hours, 24)
        if (not brief):
            if days:
                fmt = '{d} days, {h} hours, {m} minutes, and {s} seconds'
            else:
                fmt = '{h} hours, {m} minutes, and {s} seconds'
        else:
            fmt = '{h}h {m}m {s}s'
            if days:
                fmt = '{d}d ' + fmt
        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    @commands.command(aliases=["about"])
    async def botinfo(self, ctx):
        'Gives Bot Info'

        all_guilds = []
        memory_usage = self.process.memory_full_info().uss / (1024 ** 2)
        uptime = self.get_uptime(brief=True)
        for guild in self.bot.guilds:
            all_guilds.append(guild)
        total_members = sum(1 for _ in self.bot.get_all_members())
        capn = self.bot.get_user(422181415598161921)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        length=0
        for f in os.listdir(dir_path):
            if not f.endswith(".py"):
                continue
            else:
                with open(dir_path+"/"+f , 'r', encoding="utf8") as b:
                    lines = b.readlines()
                    length+=len(lines)
        repo = git.Repo(r"/home/zachary/FoodBot.git")
        commit = repo.head.commit.message    
        em = discord.Embed(title = "Bot Info", description = f"[Bot Invite](https://discordapp.com/oauth2/authorize?&client_id={self.bot.user.id}&scope=bot&permissions=104164673) | [Support Server](https://discord.gg/5ZGbuGq) | [DBL](https://discordbots.org/bot/528131615680102410) | [DBG](https://discordbots.group/bot/528131615680102410) | [Source Code](https://github.com/CapnS/FoodBot) | [Patreon](https://www.patreon.com/capn)")
        em.color = discord.Color.gold()
        em.add_field(name='Guilds', value=str(len(all_guilds)))
        em.add_field(name = "Users", value = str(total_members))
        em.add_field(name='Commands Run', value=str(self.bot.counter))
        em.add_field(name='Process Stats', value=f'''{memory_usage:.2f} MiB\n{psutil.cpu_percent()}% CPU''')
        em.add_field(name='Uptime', value=uptime)
        em.add_field(name = "Prefixes", value = f"``food!``")
        em.add_field(name="Coded By", value = capn.mention)
        em.add_field(name="Lines of Code",value = length)
        em.add_field(name="Latest Commit",value = f"```css\n{commit}\n```")
        em.set_footer(text='Requested by '+ctx.author.name, icon_url=ctx.author.avatar_url)
        em.set_thumbnail(url=self.bot.user.avatar_url)
        em.set_image(url="https://discordbots.org/api/widget/528131615680102410.png")
        await ctx.send(content=None, embed=em)

    @commands.command()
    async def source(self, ctx, command: str = None):
        """Get the bot's source link for a command or the whole source"""

        source_url = "https://github.com/CapnS/FoodBot"
        if command is None:
            return await ctx.send(source_url)
        

        obj = self.bot.get_command(command.replace('.', ' '))
        if obj is None:
            return await ctx.send('Could not find command.')

        src = obj.callback.__code__
        lines, firstlineno = inspect.getsourcelines(src)
        if not obj.callback.__module__.startswith('discord'):
            location = os.path.relpath(src.co_filename).replace('\\', '/')
        else:
            location = obj.callback.__module__.replace('.', '/') + '.py'
            source_url = "https://github.com/CapnS/FoodBot"

        await ctx.send(f"<{source_url}/tree/master/{location}/#L{firstlineno}-L{firstlineno + len(lines) - 1}>")

    @commands.command(aliases = ["vote", "dbl"])
    async def upvote(self, ctx):
        """Sends a link to upvote the bot"""
        await ctx.send("https://discordbots.org/bot/528131615680102410/vote")

    @commands.command()
    async def donate(self, ctx):
        """Sends a link to donate to me"""
        await ctx.send("https://www.patreon.com/capn")

    @commands.command()
    async def invite(self, ctx):
        """Sends a link to invite the bot"""
        await ctx.send(f"https://discordapp.com/oauth2/authorize?&client_id={self.bot.user.id}&scope=bot&permissions=104164673")

    @commands.command(aliases = ["support"] )
    async def server(self, ctx):
        """Sends a link to join the support server"""
        await ctx.send("https://discord.gg/5ZGbuGq")
        
def setup(bot):
    bot.add_cog(Info(bot))
