import discord
from discord.ext import commands
import random
import asyncio
import datetime
import ujson

class Restaurants(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def restaurant(self, ctx, city, rand=None, *, query=None):
        '''Returns details about a restaurant from the city/location and (optional) query of a search keyword'''
        key = await self.bot.db.fetchval("SELECT zomato_key from keys;")
        headers = {"user_key":key}
        async with self.bot.session.get("https://developers.zomato.com/api/v2.1/locations?query="+city, headers=headers) as r:
            data = await r.json(loads=ujson.loads)
        try:
            entity_type = str(data["location_suggestions"][0]["entity_type"])
            entity_id = str(data["location_suggestions"][0]["entity_id"])
        except IndexError:
            return await ctx.send("This city/location was not found.")
        else:
            sort = random.choice(["cost","rating"])
            order = random.choice(["asc","dec"])
            try:
                if query:
                    if rand:
                        if rand.lower() not in ("true", "false"):
                            query = rand + " " + query
                            r = False
                        else:
                            rand = rand.capitalize() == "True"
                            r = True
                    else:
                        r = False
                    query = query.replace(" ", "%20")
                    if r and not rand:
                        async with self.bot.session.get("https://developers.zomato.com/api/v2.1/search?entity_type="+entity_type+"&entity_id="+entity_id+"&q="+query, headers=headers) as r:
                            data = await r.json(loads=ujson.loads)
                            restaurant = data["restaurants"][0]["restaurant"]                            
                    else:
                        async with self.bot.session.get("https://developers.zomato.com/api/v2.1/search?entity_type="+entity_type+"&sort="+sort+"&order="+order+"&entity_id="+entity_id+"&q="+query, headers=headers) as r:
                            data = await r.json(loads=ujson.loads)
                            restaurant = random.choice(data["restaurants"])["restaurant"]    
                else:
                    async with self.bot.session.get("https://developers.zomato.com/api/v2.1/search?entity_type="+entity_type+"&sort="+sort+"&order="+order+"&entity_id="+entity_id, headers=headers) as r:
                        data = await r.json(loads=ujson.loads)
                        restaurant = random.choice(data["restaurants"])["restaurant"]
            except IndexError:
                if query:
                    return await ctx.send("No restaurants were found with that query in that city/location.")
                else:
                    return await ctx.send("No restaurants were found in that city/location.")
        name = restaurant["name"]
        url = restaurant["url"]
        restaurant_id = restaurant["id"]
        address = restaurant["location"]["address"]
        cuisine = restaurant["cuisines"]
        cost = restaurant["average_cost_for_two"]
        color = int(restaurant["user_rating"]["rating_color"], 16)
        rating = restaurant["user_rating"]["aggregate_rating"]
        async with self.bot.session.get("https://developers.zomato.com/api/v2.1/reviews?res_id="+restaurant_id, headers=headers) as r:
            data = await r.json(loads=ujson.loads)
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
            rating = str(review["rating"])
            rating_text = review["rating_text"]
            review_text = review["review_text"]
            timestamp = datetime.datetime.fromtimestamp(review["timestamp"]).strftime('%b %d, %Y')
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

    @commands.command(aliases=['reviews', 'yelpreviews', 'yr'])
    async def yelp(self, ctx, location, *, term):
        '''Looks for yelp review about restaurants matching the given term in the given location'''
        key = await self.bot.db.fetchval("SELECT yelp_key from keys;")
        authorization = {'Authorization': key}
        async with self.bot.session.get('https://api.yelp.com/v3/businesses/search?term='+term+'&location='+location, headers=authorization) as r:
            try:
                data = await r.json(loads=ujson.loads)
                business = data['businesses'][0]
                business_id = business['id']
                name = business['name']
                address = business['location']['address1'] + ' ' + business['location']['zip_code'] + ', ' + business['location']['city']
                url = business['url']
                image = business['image_url']
            except ValueError:
                return await ctx.send("No restaurants found.")
        async with self.bot.session.get('https://api.yelp.com/v3/businesses/'+business_id+'/reviews', headers=authorization) as r:
            try:
                data = await r.json(loads=ujson.loads)
                reviews = data['reviews']
            except ValueError:
                return await ctx.send("No reviews found.")
        green = discord.Color.green()
        em = discord.Embed(title=name, description=address, color=green, url=url)
        em.set_image(url=image)
        for review in reviews:
            user_name = review['user']['name']
            rating = review['rating']
            text = review['text']
            created = review['time_created']
            message = text + "\n    -" + user_name + " | " + created
            em.add_field(name=rating, value=message, inline=False)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Restaurants(bot))
