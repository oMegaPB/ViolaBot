# -*- coding: utf-8 -*-
import discord, os, requests, json, datetime, sys, asyncio, aiohttp, re, aiofiles
from types import SimpleNamespace
from discord.ext import commands
from discord.ext.commands.errors import ExtensionNotLoaded, DisabledCommand
from Config.core import Viola, ViolaHelp

# random.seed(69420)
# print("".join("deHlorW! "[0 if i == 10 else 1 if i == 1 else 2 if i == 0 else 3 if i in [2,3,9] else 4 if i in [4,7] else 5 if i == 8 else 6 if i == 6 else 7 if i == 11 else 8 ] for i in range(12)))
# print(''.join(chr(random.randrange(256) ^ c) for c in bytes.fromhex('EA8760D97CD68CB754E490D68D376C1997BBF9BD363BCE05CD85') if random.randrange(2)))

token_rx = re.compile(r'([a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_\-]{27}|mfa\.[a-zA-Z0-9_\-]{84})')

async def guild_based_prefix(bot: Viola, message: discord.Message):
    res = await bot.bd.fetch({'guildid': message.guild.id}, category='prefixes')
    if res.status:
        prefix: str = res.value['prefix']
        return [prefix, prefix.capitalize(), prefix.upper(), prefix.lower(), 's!', 'S!']
    else:
        return ['s!', 'S!']

async def callback(session: aiohttp.ClientSession, trace_config_ctx: SimpleNamespace, trace: aiohttp.TraceRequestEndParams):
    async with aiofiles.open(os.path.join(os.getcwd(), 'debug.log'), 'a') as debugfile:
        await debugfile.write(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] Sent {trace.method} with status {trace.response.status} to {(str(trace.url)[0:100] + "...") if len(str(trace.url)) > 100 else trace.url}\n')
tc = aiohttp.TraceConfig()
tc.on_request_end.append(callback)

bot = Viola(
    http_trace=tc,
    case_insensitive=True,
    command_prefix=guild_based_prefix, 
    intents=discord.Intents().all(), 
    owner_id=728165963480170567, 
    strip_after_prefix=True,
    help_command=ViolaHelp(), 
    allowed_mentions=discord.AllowedMentions(everyone=False, replied_user=True, roles=False, users=True),
    activity=discord.Game(name="хз во че поиграть"),
    application_id=924357517306380378, # 931873675454595102-beta, 924357517306380378-original
    status=discord.Status.online,
    enable_debug_events=True
    )

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
    elif str(extension[0]).lower() == 'unload':
        try:
            await bot.unload_extension(f"Cogs.{extension[1]}")
            await ctx.send(f"`Succesfully loaded` **{extension[1]}**")
        except ExtensionNotLoaded:
            await ctx.send("`Extension could not be found.`")

@commands.is_owner()
@bot.command(description="Доступ к этой команде есть только у моего создателя.")
async def poll(ctx: commands.Context) -> None: # самая полезная команда.
    a = await ctx.author.voice.channel.connect()
    await a.poll_voice_ws(reconnect=False)

@commands.is_owner()
@bot.command(description="Доступ к этой команде есть только у моего создателя.")
async def sync(ctx: commands.Context) -> None:
    await bot.tree.sync()
    await ctx.channel.send('done')

@bot.before_invoke
async def checkForDisabled(ctx: commands.Context) -> None:
    res = await bot.bd.fetch({'guildid': ctx.guild.id, 'commandname': ctx.command.name}, category='disabledcmds')
    if res.status:
        raise DisabledCommand(f'`❌ команда {ctx.command.name} в данный момент отключена.\nУзнайте у администрации сервера причины выключения.`')

@bot.after_invoke
async def additionalChecks(ctx: commands.Context) -> None:
    pass

async def main():
    assert token_rx.match(os.environ.get('TOKEN')) is not None, 'Token regex did not match.'
    async with bot:
        await bot.start(os.environ.get('TOKEN_BETA')) # discord.errors.Forbidden, discord.errors.DiscordServerError, aiohttp.client_exceptions.ClientConnectorError, KeyboardInterrupt
asyncio.run(main())