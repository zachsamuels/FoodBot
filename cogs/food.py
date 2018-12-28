import discord
from discord.ext import commands
import aiohttp
import random

class Food:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = ["fp", "foodporn"])
    async def food(self, ctx):
        """Get a random r/FoodPorn Image"""
        data = await self.bot.db.fetchrow("SELECT * FROM keys")
        client_id = data["imgur_id"]
        headers = {"Authorization" : "Client-ID "+ client_id}
        async with aiohttp.ClientSession() as ses:
            async with ses.get("https://api.imgur.com/3/gallery/r/foodporn/", headers=headers) as d:
                j = await d.json()
            await ses.close()
        x = random.choice(j["data"])
        url = x["link"]
        name = x["title"]
        blue = discord.Color.blue()
        e = discord.Embed(title = "Food Porn", description = name, url = url, color = blue)
        e.set_image(url=url)
        e.set_footer(text="Requested by "+ ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=e)

def setup(bot):
    bot.add_cog(Food(bot))