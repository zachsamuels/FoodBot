import discord
from discord.ext import commands
import asyncio
import aiohttp

class Recipe:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def recipe(self, ctx, *, search):
        data = await self.bot.db.fetchrow("SELECT * FROM keys")
        app_id = data['recipe_id']
        app_key = data['recipe_key']
        async with aiohttp.ClientSession() as ses:
            async with ses.get("https://api.edamam.com/search?q="+search+"&app_id="+app_id+"&app_key="+app_key) as r:
                t = await r.json()
            await ses.close()
        if not t['hits']:
            return await ctx.send("No Recipes Found")
        recipe = t['hits'][0]["recipe"]
        name = recipe['label']
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
        general.add_field(name= "Ingredients", value=ingredients)
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
                    if x == 0:
                        x = 1
                    else: 
                        x = 0
                em = embeds[x]
                await message.edit(embed = em)    

def setup(bot):
    bot.add_cog(Recipe(bot))