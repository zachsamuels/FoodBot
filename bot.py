import discord
from discord.ext import commands
import asyncpg
import asyncio
import time

bot = commands.Bot(command_prefix="f!")

async def set_up_token():
    credentials = {"user": "zachary", "password": "capn", "database": "foodbot", "host": "127.0.0.1"}
    db = await asyncpg.create_pool(**credentials) 
    data = await db.fetchrow("SELECT * FROM keys;")
    global TOKEN
    TOKEN = data["token"]

@bot.event
async def on_ready():
    bot.load_extension("jishaku")
    bot.load_extension("cogs/recipes")
    bot.load_extension("cogs/info")
    credentials = {"user": "zachary", "password": "capn", "database": "foodbot", "host": "127.0.0.1"}
    bot.db = await asyncpg.create_pool(**credentials) 
    bot.launch_time = time.time()
    bot.counter = 0
    print("Ready!")

@bot.event
async def on_message(message):
    if not message.author.bot:
        await bot.process_commands(message)

@bot.event
async def on_command():
    bot.counter+=1

bot.loop.run_until_complete(set_up_token())
bot.run(TOKEN)