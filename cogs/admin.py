import discord
from discord.ext import commands
import subprocess
import aiohttp

class Admin:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def mellow(self, ctx, *, code):
        with open("home/zachary/mellow/test.mlw", 'w') as f:
            f.write(code)
            f.close()
        def runshell(code):
            with subprocess.Popen(["/bin/bash", "-c", "python3 home/zachary/mellow/mellow.py home/zachary/mellow/test.mlw"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
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
                await ctx.send("**:x: | Couldn't upload to Mystbin.**") 

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
            await ctx.send("Deleted "+str(len(deleted) - 1)+" messages.")

def setup(bot):
    bot.add_cog(Admin(bot))