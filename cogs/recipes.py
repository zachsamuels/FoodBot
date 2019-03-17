import discord
from discord.ext import commands
import asyncio
import aiohttp
import random
import re

class Recipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def recipe(self, ctx, *, search):
        """Gives a recipe for your search along with Nutritional Facts"""
        data = await self.bot.db.fetchrow("SELECT * FROM keys")
        app_ids = data['recipe_id']
        app_keys = data['recipe_key']
        f = False
        c = 0
        while not f:
            try:
                app_id = app_ids[c]
                app_key = app_keys[c]
            except:
                return await ctx.send("Ratelimited, try again in one minute.")
            else:
                async with self.bot.session.get("https://api.edamam.com/search?q="+search+"&app_id="+app_id+"&app_key="+app_key) as r:
                    try:
                        t = await r.json()
                    except:
                        c+=1
                    else:
                        f = True
        if not t['hits']:
            return await ctx.send("No Recipes Found")
        recipe = t['hits'][0]["recipe"]
        name = recipe['label']
        image = recipe['image']
        time = str(int(recipe['totalTime'])) + " minutes"
        servings = str(int(recipe['yield'])) + " servings"
        url = recipe['shareAs']
        ingredients = "- " + "\n- ".join(recipe['ingredientLines'])
        diets = ", ".join(recipe['dietLabels'])
        health = ", ".join(recipe["healthLabels"])
        calories = str(int(recipe['calories']))
        nutrients = recipe['totalNutrients']
        nuts = []
        for entry in nutrients:
            e = nutrients[entry]
            nuts.append(e["label"]+" - " + str(round(e["quantity"],1)) + e["unit"])
        n = "\n".join(nuts)
        d = diets + ", " + health if diets else health 
        green = discord.Color.green()
        general = discord.Embed(title = name, description = "General Info", color = green, url = url)
        general.add_field(name= "Time to Make", value= time)
        general.add_field(name="Servings",value=servings)
        general.add_field(name= "Ingredients", value=ingredients, inline = False)
        general.set_thumbnail(url=image)
        nutrition = discord.Embed(title = name, description="Nutrition Facts",url=url,color=green)
        nutrition.add_field(name="Health and Diet",value=d)
        nutrition.add_field(name="Calories", value=calories)
        nutrition.add_field(name="Contains", value = n, inline = False)
        emojis = ("\U000025c0","\U000025b6","\U000023f9")
        def check(reaction,user):
            return user == ctx.author and str(reaction.emoji) in emojis
        x = 0
        embeds = {0:general,1:nutrition}
        message = await ctx.send(embed=general)
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
                    x = int(not x)
                em = embeds[x]
                await message.edit(embed = em)    

    @commands.command()
    async def tasty(self, ctx):
        async with self.bot.session.get("https://www.instagram.com/buzzfeedtasty/") as r:
            text = await r.text()
        x = re.findall('"shortcode":".{11,12}"', text)
        codes = list()
        for z in x:
            z = "{"+z+"}"
            y = eval(z)
            codes.append(y["shortcode"])
        code = random.choice(codes)
        await ctx.send("https://www.instagram.com/p/"+code+"/")


def setup(bot):
    bot.add_cog(Recipe(bot))