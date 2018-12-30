import discord
from discord.ext import commands
import asyncpg
import asyncio
import time
import aiohttp

bot = commands.Bot(command_prefix="food!")

async def set_up_token():
    credentials = {"user": "zachary", "password": "capn", "database": "foodbot", "host": "127.0.0.1"}
    db = await asyncpg.create_pool(**credentials) 
    data = await db.fetchrow("SELECT * FROM keys;")
    global TOKEN
    TOKEN = data["token"]

@bot.command()
async def echo(ctx, *, repeat):
    await ctx.send(repeat)
    
@bot.command()
async def ping(ctx):
    'Pings Bot'
    channel = ctx.channel
    t1 = time.perf_counter()
    await channel.trigger_typing()
    t2 = time.perf_counter()
    latency = round(bot.latency *1000)
    t = round((t2-t1)*1000)
    green = discord.Color.green()
    desc=f":heartbeat: **{latency}**ms \n :stopwatch: **{t}**ms"
    em = discord.Embed(title = ":ping_pong: Pong",description = desc, color = green)
    em.set_footer(text=f"Requested by {ctx.author.name}",icon_url=ctx.author.avatar_url)
    await ctx.send(embed=em)
    
@bot.event
async def on_ready():
    bot.load_extension("jishaku")
    bot.load_extension("cogs.recipes")
    bot.load_extension("cogs.info")
    bot.load_extension("cogs.food")
    bot.load_extension("cogs.errors")
    credentials = {"user": "zachary", "password": "capn", "database": "foodbot", "host": "127.0.0.1"}
    bot.db = await asyncpg.create_pool(**credentials) 
    bot.launch_time = time.time()
    bot.counter = 0
    bot.session = aiohttp.ClientSession()
    await bot.change_presence(activity=discord.Game(name="food!help")) 
    print("Ready!")

@bot.event
async def on_message(message):
    if not message.author.bot:
        await bot.process_commands(message)

@bot.event
async def on_command(ctx):
    bot.counter+=1

@bot.event
async def on_message_edit(before,after):
    if not after.author.bot:
        await bot.process_commands(after)

bot.loop.run_until_complete(set_up_token())
bot.run(TOKEN)
