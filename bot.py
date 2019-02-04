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
    """Repeats your Message"""
    repeat = repeat.replace("@", "@​")
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
    exts = ["recipes", "info", "food", "errors", "admin"]
    for ext in exts:
        bot.load_extension("cogs."+ext)
    credentials = {"user": "zachary", "password": "capn", "database": "foodbot", "host": "127.0.0.1"}
    bot.db = await asyncpg.create_pool(**credentials) 
    bot.launch_time = time.time()
    bot.counter = 0
    bot.session = aiohttp.ClientSession()
    bot.owner = bot.get_user(422181415598161921)
    await bot.change_presence(activity=discord.Game(name="food!help")) 
    print("Ready!")

@bot.event
async def on_message(message):
    if message.content in ("<@528131615680102410>", "@Food Bot"):
        await message.channel.send("Hello! I am a bot for foodies on discord. To learn how to use me, type food!help")
    if not message.author.bot:
        await bot.process_commands(message)

@bot.event
async def on_command(ctx):
    bot.counter+=1
    w = await bot.get_webhook_info(541858297133924356)
    em = discord.Embed(title = "Command", description = "```"+ctx.message.content+"```")
    if ctx.guild:
        em.add_field(name = "Info", value = "Guild: "+ ctx.guild.name + "(" + str(ctx.guild.id) + ")\nAuthor: "+str(ctx.author) +"("+str(ctx.author.id)+")")
    else:
        em.add_field(name = "Info", value = "Guild: Private Messages\nAuthor: "+str(ctx.author) +"("+str(ctx.author.id)+")")        
    em.set_author(name = str(ctx.author), icon_url=ctx.author.avatar_url)
    await w.send(embed=em)

@bot.event
async def on_message_edit(before,after):
    if not after.author.bot:
        await bot.process_commands(after)

async def update_guild_count():
    await bot.wait_until_ready()
    await asyncio.sleep(10)
    while not bot.is_closed():
        data = await bot.db.fetchrow("SELECT * FROM keys;")
        key = data["dbl_key"]
        auth = {"Authorization": key}
        server_count = {"server_count":len(bot.guilds)}
        async with aiohttp.ClientSession(headers=auth) as session:
            await session.post(f"https://discordbots.org/api/bots/{bot.user.id}/stats", data=server_count)
        await asyncio.sleep(86400)

bot.loop.run_until_complete(set_up_token())
bot.loop.create_task(update_guild_count())
bot.run(TOKEN)
