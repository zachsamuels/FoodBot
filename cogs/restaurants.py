import discord
from discord.ext import commands
import random

class Restaurants(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def restaurant(self, ctx,*, location):
        '''Gives information on a random restaurant from the location given'''
        data = await self.bot.db.fetchrow("SELECT * from keys;")
        key = data["zomato_key"]
        headers = {"user_key":key}
        async with self.bot.session.get("https://developers.zomato.com/api/v2.1/locations?count=100&query="+location, headers=headers) as r:
            data = await r.json()
            city = str(data["location_suggestions"][0]["city_id"])
        async with self.bot.session.get("https://developers.zomato.com/api/v2.1/search?entity_type=city&entity_id="+city, headers=headers) as r:
            data = await r.json()
            restaurant = random.choice(data["restaurants"])["restaurant"]
        name = restaurant["name"]
        url = restaurant["url"]
        address = restaurant["location"]["address"]
        cuisine = restaurant["cuisines"]
        cost = str(restaurant["average_cost_for_two"])
        color = int(restaurant["user_rating"]["rating_color"], 16)
        rating = str(restaurant["user_rating"]["aggregate_rating"])
        em = discord.Embed(title=name, description="Cuisine: "+cuisine, url=url, color=discord.Color(color))
        em.add_field(name="Address", value=address)
        em.add_field(name="Avg. Cost per 2 People", value=cost)
        em.add_field(name="Rating", value=rating, inline=False)
        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Restaurants(bot))