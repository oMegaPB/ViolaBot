# -*- coding: utf-8 -*-
import discord, os, requests, json, datetime, sys, asyncio, traceback, random
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.ext.commands.errors import ExtensionNotLoaded
from Config.settings import token
from aiohttp.client_exceptions import ClientConnectorError
intents = discord.Intents().all()

guild_pref = {814402686157193236: "?"}
def guild_based_prefix(bot, message: discord.Message):
    return guild_pref.get(message.guild.id, "s!")

bot = commands.Bot(case_insensitive=True, command_prefix=guild_based_prefix, intents=intents, owner_id=728165963480170567, strip_after_prefix=True)
bot.remove_command("help")
async def loadcogs():
    for filename in os.listdir(os.path.dirname(os.path.realpath(__file__)) + '\\Cogs'):
        if filename.endswith(".py"):
            await bot.load_extension(fr"Cogs.{filename[:-3]}")
asyncio.run(loadcogs())

@bot.command()
async def cog(ctx: commands.Context, *extension):
    if ctx.author.id == 728165963480170567:
        if str(extension[0]).lower() == "reload":
            try:
                await bot.reload_extension(f"Cogs.{extension[1]}")
                await ctx.send(f"`Succesfully reloaded` **{extension[1]}**")
            except ExtensionNotLoaded:
                await ctx.send("`Extension could not be found.`")
        elif str(extension[0]).lower() == 'load':
            try:
                await bot.load_extension(f"Cogs.{extension[1]}")
                await ctx.send(f"`Succesfully loaded` **{extension[1]}**")
            except ExtensionNotLoaded:
                await ctx.send("`Extension could not be found.`")

try:
    bot.run(token, log_level=0)
except ClientConnectorError:
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [Viola/INFO]: Discord Bot Start Failed... (Connection issues).")
except discord.errors.DiscordServerError:
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [Viola/INFO]: Discord Bot Start Failed... (Discord Servers are Unavailable).")
except discord.errors.Forbidden:
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [Viola/INFO]: Discord Bot Start Failed... (403 Forbidden).")
except discord.errors.LoginFailure:
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [Viola/INFO]: Discord Bot Start Failed... (Invalid Token).")