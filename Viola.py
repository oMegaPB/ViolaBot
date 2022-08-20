# -*- coding: utf-8 -*-
import discord, os, requests, json, datetime, sys, asyncio, traceback, random, typing, time
from discord.ext import commands
from discord.ext.commands.errors import ExtensionNotLoaded
from aiohttp.client_exceptions import ClientConnectorError
from Config.core import Viola, CommandDisabled, ViolaHelp

loop = asyncio.new_event_loop()

async def guild_based_prefix(bot: Viola, message: discord.Message):
    res = await bot.bd.fetch({'guildid': message.guild.id}, category='prefixes')
    if res.status:
        prefix: str = res.value['prefix']
        return [prefix, prefix.capitalize(), prefix.upper(), prefix.lower(), 's!', 'S!']
    else:
        return ['s!', 'S!']

bot = Viola(
    case_insensitive=True,
    command_prefix=guild_based_prefix, 
    intents=discord.Intents().all(), 
    owner_id=728165963480170567, 
    strip_after_prefix=True,
    help_command=ViolaHelp(), 
    max_messages=5000,
    allowed_mentions=discord.AllowedMentions(everyone=False, replied_user=True, roles=False, users=True),
    activity=discord.Game(name="Скайрим"),
    application_id=924357517306380378, # 931873675454595102-beta, 924357517306380378-original
    status=discord.Status.online,
    enable_debug_events=True
    )

async def loadcogs() -> None:
    for filename in os.listdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Cogs')):
        if filename.endswith(".py"):
            if filename == 'music.py':
                continue
            await bot.load_extension(fr"Cogs.{filename[:-3]}")
loop.run_until_complete(loadcogs())

@commands.is_owner()
@bot.command(description="Доступ к этой команде есть только у моего создателя.")
async def cog(ctx: commands.Context, *extension):
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

@commands.is_owner()
@bot.command(description="Доступ к этой команде есть только у моего создателя.")
async def poll(ctx: commands.Context) -> None: # самая полезная команда.
    a = await ctx.author.voice.channel.connect()
    await a.poll_voice_ws(reconnect=False)

@bot.before_invoke
async def checkForDisabled(ctx: commands.Context) -> None:
    command = ctx.command.name
    res = await bot.bd.fetch({'guildid': ctx.guild.id, 'commandname': command}, category='disabledcmds')
    if res.status:
        raise CommandDisabled(f'`❌ команда {command} в данный момент отключена.\nУзнайте у администрации сервера причины выключения.`')

@bot.after_invoke
async def additionalChecks(ctx: commands.Context) -> None:
    pass

try:
    loop.run_until_complete(bot.start(os.environ.get('TOKEN_BETA')))
except KeyboardInterrupt:
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{bot.user.name}/INFO]: Discord Bot Stopped... (KeyboardInterrupt).")
except ClientConnectorError:
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{bot.user.name}/INFO]: Discord Bot Start Failed... (Connection issues).")
except discord.errors.DiscordServerError:
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{bot.user.name}/INFO]: Discord Bot Start Failed... (Discord Servers are Unavailable).")
except discord.errors.Forbidden:
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{bot.user.name}/INFO]: Discord Bot Start Failed... (403 Forbidden).")
except discord.errors.LoginFailure:
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{bot.user.name}/INFO]: Discord Bot Start Failed... (Invalid Token).")