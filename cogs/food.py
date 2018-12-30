import discord
from discord.ext import commands
import aiohttp
import random
import asyncio

class Food:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = ["fp"])
    async def foodporn(self, ctx):
        """Get a random r/FoodPorn Image"""
        data = await self.bot.db.fetchrow("SELECT * FROM keys")
        client_id = data["imgur_id"]
        headers = {"Authorization" : "Client-ID "+ client_id}
        async with self.bot.session.get("https://api.imgur.com/3/gallery/r/foodporn/", headers=headers) as d:
            j = await d.json()
        x = random.choice(j["data"])
        url = x["link"]
        name = x["title"]
        blue = discord.Color.blue()
        e = discord.Embed(title = "Food Porn", description = name, url = url, color = blue)
        e.set_image(url=url)
        e.set_footer(text="Requested by "+ ctx.author.name, icon_url=ctx.author.avatar_url)
        message = await ctx.send(embed=e)
        emojis = ("\U000025b6","\U000023f9")
        def check(reaction,user):
            return user == ctx.author and str(reaction.emoji) in emojis
        for emoji in emojis:
            await message.add_reaction(emoji)
        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add",check=check, timeout=60)
            except asyncio.TimeoutError:
                for emoji in emojis:
                    await message.remove_reaction(emoji, ctx.me)
                return
            else:
                try:
                    await message.remove_reaction(r,u)
                except:
                    pass
                if str(r.emoji) == "\U000023f9":
                    return await message.delete()
                else:
                    x = random.choice(j["data"])
            url = x["link"]
            name = x["title"]
            blue = discord.Color.blue()
            e = discord.Embed(title = "Food Porn", description = name, url = url, color = blue)
            e.set_image(url=url)
            e.set_footer(text="Requested by "+ ctx.author.name, icon_url=ctx.author.avatar_url)
            await message.edit(embed=e)

    @commands.command(aliases = ["fs","foodsearch","nutrition"])
    async def food(self, ctx, *, search):
        data = await self.bot.db.fetchrow("SELECT * FROM keys")
        app_id = data['food_id']
        app_key = data['food_key']
        async with self.bot.session.get("https://api.edamam.com/api/nutrition-data?ingr="+search+"&app_id="+app_id+"&app_key="+app_key) as r:
            t = r.text
            await ctx.send(t)
        url = t.get("uri")
        diet = t.get("dietLabels")
        health = t.get("healthLabels")
        calories = t.get("calories")
        cautions = t.get("cautions")
        n = t.get("totalNutrients")
        nuts = list()
        for x in n:
            e = n.get(x)
            nuts.append(e.get("label") + " - " + str(int(e.get("quantity"))) + e.get("unit"))
        nutrients = " - ".join(nuts)
        d = ", ".join(health) + ", " + ", ".join(diet) if diet else ", ".join(health)
        c = ", ".join(cautions)
        blue = discord.Color.blue()
        e = discord.Embed(title="Nutrition Facts",description = search.title(), url = url, color = blue)
        e.add_field(name= "Calories",value = calories)
        e.add_field(name="Diet and Health Labels", value = d)
        e.add_field(name="Cautions", value = c)
        e.add_field(name ="Nutrients",value = nutrients, inline = False)
        e.set_footer(text="Requested by "+ ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=e)

def setup(bot):
    bot.add_cog(Food(bot))