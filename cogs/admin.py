import discord
from discord.ext import commands
import subprocess
import aiohttp
import datetime
import parsedatetime

async def is_admin(ctx):
    return ctx.author.id in (422181415598161921, 300088143422685185)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cal = parsedatetime.Calendar()

    @commands.command()
    @commands.check(is_admin)
    async def mellow(self, ctx, *, code):
        with open("/home/zachary/mellow/test.mlw", 'w') as f:
            f.write(code)
            f.close()
        def runshell(code):
            with subprocess.Popen(["/bin/bash", "-c", "python3 /home/zachary/mellow/mellow.py /home/zachary/mellow/test.mlw"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
                out, err = process.communicate(timeout=60)
                if err:
                    return [f"```fix\n{code}``` ```fix\n-- stdout --\n\n{out.decode()}``` ```fix\n-- stderr --\n\n{err.decode()}```", out.decode(), err.decode()]
                else:
                    return [f"```fix\n{code}``` ```fix\n-- stdout --\n\n{out.decode()}```", out.decode(), err.decode()]
        result = await self.bot.loop.run_in_executor(None, runshell, code)
        try:
            await ctx.send(result[0])
        except Exception:
            await ctx.send(f"**:arrow_up: | Looks like output is too long. Attempting upload to Mystbin.**")
            try:
                async with aiohttp.ClientSession().post("http://mystb.in/documents", data=f"{result[1]}\n\n\n\n{result[2]}".encode('utf-8')) as post:
                    post = await post.json()
                    await ctx.send(f"**:white_check_mark: | http://mystb.in/{post['key']}**")
            except Exception:
                print(result[0])
                await ctx.send("**:x: | Couldn't upload to Mystbin.**") 

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def cleanup(self, ctx, limit:int=25):
        """
            Cleans up the chat of bot messages or messages that used a bot command.
            (Only looks through the number of messages specified in the limit parameter,
            which defaults to 25 messages.)
        """
        def check(message):
            return message.content.startswith("food!") or message.author == self.bot.user
        try:
            deleted = await ctx.channel.purge(limit=limit+1, check=check)
        except:
            await ctx.send("Could not delete messages")
        else:
            await ctx.send("Deleted "+str(len(deleted) - 1)+" messages.")

    @commands.command()
    async def lunch(self, ctx, *, date=None):
        """
            Shows what is for lunch at Capn's School today, or on the optional date parameter.
            (Why would you use this command tbh)
        """
        async with self.bot.session.get("http://www.sagedining.com/intranet/apps/mb/pubasynchhandler.php?unitId=S0097&mbMenuCardinality=0&_=1553019503735") as r:
            data = await r.json(content_type='text/html')
        first_date = int(data['menuList'][0]['menuFirstDate'])
        if not date:
            datetime_date = datetime.datetime.now() - datetime.timedelta(hours=5)
            day = int(datetime_date.strftime('%w'))
            days = (datetime_date - datetime.datetime.fromtimestamp(first_date)).days + 1
        else:
            now = (datetime.datetime.now() - datetime.timedelta(hours=5)).strftime('%b %d, %Y')
            now, parse = self.cal.parse(now)
            time_struct, parse_strust = self.cal.parse(date, now)
            if parse_strust != 1:
                return await ctx.send("Your date string was not recognized.")
            else:
                datetime_date = datetime.datetime(*time_struct[:6])
                days = (datetime_date - datetime.datetime.fromtimestamp(first_date)).days + 1
                day = int(datetime_date.strftime('%w'))
                if days < 0:
                    return await ctx.send("The date given is before the first recorded lunch this year.")
        weeks, d = divmod(days, 7)
        try:
            today = data['menu']['menu']['items'][weeks][day][1]
        except IndexError:
            return await ctx.send("This date is too far in the future for a lunch to be planned.")
        soups = today[0]
        salad = today[1]
        deli = today[2]
        main = today[3]
        dessert = today[8]
        categories = [soups, salad, deli, main, dessert]
        names = ["Soups", "Salad Bar", "Deli Bar", "Main Course", "Dessert"]
        color = discord.Color.green()
        em = discord.Embed(title="Menu For Lunch", description=datetime_date.strftime('%b %d, %Y'), color=color)
        for i, category in enumerate(categories):
            name = names[i]
            foods = ""
            for food in category:
                foods += food["a"] + "\n"
            if foods:
                em.add_field(name=name, value=foods, inline=False)
        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Admin(bot))