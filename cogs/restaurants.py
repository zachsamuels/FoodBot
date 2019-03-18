import discord
from discord.ext import commands
import random
import asyncio
import datetime

class Restaurants(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def restaurant(self, ctx, *, location):
        data = await self.bot.db.fetchrow("SELECT * from keys;")
        key = data["zomato_key"]
        headers = {"user_key":key}
        async with self.bot.session.get("https://developers.zomato.com/api/v2.1/locations?query="+location, headers=headers) as r:
            data = await r.json()
            city = str(data["location_suggestions"][0]["city_id"])
        start = str(random.randint(0,80))
        sort = random.choice(["cost","rating"])
        order = random.choice(["asc","dec"])
        async with self.bot.session.get("https://developers.zomato.com/api/v2.1/search?entity_type=city&sort="+sort+"&order="+order+"&start="+start+"&entity_id="+city, headers=headers) as r:
            data = await r.json()
            restaurant = random.choice(data["restaurants"])["restaurant"]
        name = restaurant["name"]
        url = restaurant["url"]
        restaurant_id = restaurant["id"]
        address = restaurant["location"]["address"]
        cuisine = restaurant["cuisines"]
        cost = restaurant["average_cost_for_two"]
        color = int(restaurant["user_rating"]["rating_color"], 16)
        rating = restaurant["user_rating"]["aggregate_rating"]
        async with self.bot.session.get("https://developers.zomato.com/api/v2.1/reviews?res_id="+restaurant_id, headers=headers) as r:
            data = await r.json()
        try:
            reviews = random.sample(data["user_reviews"], 5)
        except ValueError:
            reviews = data["user_reviews"]
        em = discord.Embed(title=name, description="Cuisine: "+cuisine, url=url, color=discord.Color(color))
        em.add_field(name="Address", value=address)
        em.add_field(name="Avg. Cost per 2 People", value=cost)
        em.add_field(name="Rating", value=rating, inline=False)
        revem = discord.Embed(title=name, description="Reviews", url=url, color=discord.Color(color))
        for rev in reviews:
            review = rev["review"]
            user_name = review["user"]["name"]
            rating = review["rating"]
            rating_text = review["rating_text"]
            review_text = review["review_text"]
            timestamp = datetime.datetime(review["timestamp"]).strftime('%b %d, %Y')
            revem.add_field(name=rating+ " - " + rating_text, value= review_text + "\n" + "    -" + user_name + " | " + timestamp)
        embeds = {0:em, 1:revem}
        x = 0
        message = await ctx.send(embed=em)
        def check(reaction,user):
            return user == ctx.author and str(reaction.emoji) in emojis and reaction.message.id == message.id
        emojis = ("\U000025c0","\U000025b6","\U000023f9")
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


def setup(bot):
    bot.add_cog(Restaurants(bot))
