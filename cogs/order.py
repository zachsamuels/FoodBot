import discord
from discord.ext import commands
import datetime
from .paginator import Pages
import asyncio

class Order(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.capn = bot.get_user(422181415598161921)

    @commands.command()
    async def order(self, ctx, *, address):
        '''Searches for restaurants at the address given, and then starts an order at the restaurant chosen'''
        user = await self.bot.db.fetchrow('SELECT * FROM order_keys WHERE user_id=$1', ctx.author.id)
        if not user:
            return await ctx.send('You need an ordering account to order. Use the register command to make an account.')
        else:
            key = user['user_key']
        api_key = await self.bot.db.fetchval('SELECT eatstreet from keys')
        auth = {'X-Access-Token': api_key, 'Content-Type': 'application/json'}
        address = address.replace(' ', '+')
        async with self.bot.session.get('https://eatstreet.com/publicapi/v1/restaurant/search?method=both&street-address='+address, headers=auth) as r:
            data = await r.json()
        restaurants = dict()
        for r in data['restaurants']:
            restaurants.update({r['name']: r['apiKey']})
        p = Pages(ctx, entries=list(restaurants.keys()))
        asyncio.ensure_future(p.paginate()) 
        await ctx.send('Which restaurant is the correct one? (If your restaurant is not in here, just send `Not Found`)')
        def check(message):
            return message.author.id == ctx.author.id
        try:
            message = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            return await ctx.send('You took too long to respond, try again.')
        if message.content == 'Not Found':
            return await ctx.send("I'm sorry I wasn't able to help you find your restaurant.")
        try:
            restaurant_id = restaurants[list(restaurants.keys())[int(message.content)-1]]
        except ValueError:
            return await ctx.send('Invalid Number.')
        except IndexError:
            return await ctx.send('That Restaurant is not on the list.')
        async with self.bot.session.get('https://eatstreet.com/publicapi/v1/restaurant/'+restaurant_id+'/menu?includeCustomizations=false', headers=auth) as r:
            data = await r.json()
        categories = dict()
        for category in data:
            categories.update({category['name']: category['items']})
        all = list()
        keys = dict()
        for category in categories:
            all.append(category)
            for item in categories[category]:
                all.append(item['name'] + '-' + str(item['basePrice']))
                keys.update({
                    item['name'] + '-' + str(item['basePrice']):
                    [item['apiKey'], item['basePrice']]
                })
        p = Pages(ctx, entries=all)
        asyncio.ensure_future(p.paginate())
        order_items = list()
        price = 0
        order_keys = list()
        while True:
            await ctx.send('What number do you want? (`end` to stop)')
            try:
                message = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                return await ctx.send('You took too long to respond, try again.')
            if message.content == 'end':
                await ctx.send('Your Order:\n-'+'\n-'.join(order_items)+'\n Total Price: $'+str(price))
                break
            else:
                try:
                    next = int(message.content)
                    order_items.append(all[next-1])
                    price += keys[all[next-1]][1]
                    order_keys.append(keys[all[next-1]][0])
                except (KeyError, IndexError, ValueError):
                    await ctx.send('Invalid Option')
        orders = list()
        for order_key in order_keys:
            orders.append({
                'apiKey': order_key
            })
        order = {
            'restaurantApiKey': restaurant_id,
            'items': orders,
            'recipient': {
                'apiKey': key
            }
        }
        await ctx.send('Pickup or Delivery?')
        method = ''
        while not method in ('pickup', 'delivery'):
            try:
                message = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                return await ctx.send('You took too long to respond, try again.')
            if not message.content.lower() in ('pickup', 'delivery'):
                await ctx.send('Invalid Option, try again')
            else:
                method = message.content.lower() 
                if method == "delivery":
                    if user['address_key'] is None:
                        return await ctx.send("You don't have an Address set up with your account.") 
                    else:
                        address_key = user['address_key']  
                        order.update({'address': {'apiKey': address_key}})
                order.update({'method': method})
        await ctx.send('Cash or Card?')
        payment = ''
        while not payment in ('cash', 'card'):
            try:
                message = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                return await ctx.send('You took too long to respond, try again.')
            if not message.content.lower() in ('cash', 'card'):
                await ctx.send('Invalid Option, try again')
            else:
                payment = message.content.lower()
                if payment == "card":
                    if user['card_key'] is None:
                        return await ctx.send("You don't have a Credit Card set up with your account.")
                    else:
                        card_key = user['card_key']
                        order.update({'card': {'apiKey': card_key}})
                order.update({'payment': payment})
        tip = 0
        while not tip > 0:
            try:
                await ctx.send("What do you want to tip?")
                message = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                return await ctx.send('You took too long to respond, try again.')
            else:
                try:
                    tip = int(message.content)
                except ValueError:
                    await ctx.send("Invalid Tip.")
                else:
                    order.update({'tip': tip})
                    break
        async with self.bot.session.post('https://api.eatstreet.com/publicapi/v1/send-order', json=order, headers=auth) as r:
            try:
                data = await r.json()
                if not data['apiKey']:
                    await self.capn.send(await r.text())
                    return await ctx.send("I'm sorry, but there was an error making your order. Report this to Capn#0001")
                else:
                    await ctx.author.send('The api key for your order is `'+data['apiKey']+'`. Use this to track your order using the track_order command.')
            except:
                error = await r.text()
                await self.capn.send(error)
                return await ctx.send("I'm sorry, but there was an error making your order. `"+error+"`")

    @commands.command()
    async def register(self, ctx, old_key=None):
        '''Register your account with the ordering service'''
        if await self.bot.db.fetchrow('SELECT * FROM order_keys WHERE user_id=$1', ctx.author.id):
            return await ctx.send('You already have an account. If you would like to add a credit card or address, use the add_card or add_address comands.')
        if old_key:
            await self.bot.db.execute('INSERT INTO order_keys VALUES ($1, $2)', ctx.author.id, old_key)
            return await ctx.send('Account registered in database.')
        await ctx.send("https://foodbot.tk/?user_id="+str(ctx.author.id))

    @commands.command()
    async def add_card(self, ctx, key=None):
        '''Adds a card to your registered ordering account'''
        data = await self.bot.db.fetchrow('SELECT * FROM order_keys WHERE user_id=$1', ctx.author.id)
        if not data:
            return await ctx.send('You need an ordering account to add a credit card. Use the register command to make an account.')
        elif data['card_key'] is not None:
            return await ctx.send('You already have a credit card associated with your account. To remove this card, use the remove_card command.')
        await ctx.send("https://foodbot.tk/add_card?user_id="+str(ctx.author.id))

    @commands.command()
    async def add_address(self, ctx, key=None, street_address=None, zipcode=None, card_key=None):
        '''Adds an address to your account'''
        data = await self.bot.db.fetchrow('SELECT * FROM order_keys WHERE user_id=$1', ctx.author.id)
        if not data:
            return await ctx.send('You need a registered account to add an address. Use the register command to make an account.')
        elif data['address_key'] is not None:
            return await ctx.send('You already have an address associated with your account. To remove this address, use the remove_address command.')
        await ctx.send("https://foodbot.tk/add_address?user_id="+str(ctx.author.id))

    @commands.command()
    async def track_order(self, ctx, key):
        '''Tracks an order'''
        api_key = await self.bot.db.fetchval('SELECT eatstreet from keys')
        auth = {'X-Access-Token': api_key, 'Content-Type': 'application/json'}
        async with self.bot.session.post('https://eatstreet.com/publicapi/v1/order/'+key+'/statuses', headers=auth) as r:
            data = await r.json()
        if not data[0]['status']:
            return await ctx.send('That key does not correspond to any order that has been placed.')
        else:
            status = data[0]['status']
            changed = datetime.datetime.fromtimestamp(data[0]['date']).strftime('%b %d, %Y at %I:%M:%S%p')
            await ctx.send('Your order has been '+status+' since '+changed)

    @commands.command()
    async def remove_card(self, ctx):
        '''Removes your card api key from the database'''
        data = await self.bot.db.fetchrow('SELECT * FROM order_keys WHERE user_id=$1', ctx.author.id)
        if not data:
            return await ctx.send('You need a registered account to remove a card. Use the register command to make an account.')
        elif data['card_key'] is None:
            return await ctx.send("You don't have a card associated with your account, so no need to remove one.")
        else:
            key = data['user_key']
            card_key = data['card_key']
        api_key = await self.bot.db.fetchval('SELECT eatstreet from keys')
        auth = {'X-Access-Token': api_key, 'Content-Type': 'application/json'}
        async with self.bot.session.post('https://eatstreet.com/publicapi/v1/user/'+key+'/remove-card/'+card_key, headers=auth) as r:
            try:
                data = await r.json()
                if data.get('error') is None:
                    await self.bot.db.execute('UPDATE order_keys SET card_key=$1 WHERE user_id=$2', None, ctx.author.id)
                    return await ctx.send('Card successfully removed')
                else:
                    await self.capn.send(await r.text())
                    return await ctx.send("I'm sorry, but there was an error removing your card. Report this to Capn#0001")
            except:
                await self.capn.send(await r.text())
                return await ctx.send("I'm sorry, but there was an error removing your card. Report this to Capn#0001")

    @commands.command()
    async def remove_address(self, ctx):
        '''Removes your address api key from the database'''
        data = await self.bot.db.fetchrow('SELECT * FROM order_keys WHERE user_id=$1', ctx.author.id)
        if not data:
            return await ctx.send('You need a registered account to remove an address. Use the register command to make an account.')
        elif data['address_key'] is None:
            return await ctx.send("You don't have an address associated with your account, so no need to remove one.")
        else:
            key = data['user_key']
            card_key = data['address_key']
        api_key = await self.bot.db.fetchval('SELECT eatstreet from keys')
        auth = {'X-Access-Token': api_key, 'Content-Type': 'application/json'}
        async with self.bot.session.post('https://eatstreet.com/publicapi/v1/user/'+key+'/remove-address/'+card_key, headers=auth) as r:
            try:
                data = await r.json()
                if data.get('error') is None:
                    await self.bot.db.execute('UPDATE order_keys SET address_key=$1 WHERE user_id=$2', None, ctx.author.id)
                    return await ctx.send('Address successfully removed')
                else:
                    await self.capn.send(await r.text())
                    return await ctx.send("I'm sorry, but there was an error removing your address. Report this to Capn#0001")
            except:
                await self.capn.send(await r.text())
                return await ctx.send("I'm sorry, but there was an error removing your address. Report this to Capn#0001")

    @commands.command()
    async def delete_account(self, ctx):
        '''Deletes your account from database'''
        await self.bot.db.execute('DELETE FROM order_keys WHERE user_id=$1', ctx.author.id)
        await ctx.send('Account Deleted')

def setup(bot):
    bot.add_cog(Order(bot))