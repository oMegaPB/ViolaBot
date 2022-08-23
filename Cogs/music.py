import re
import traceback
import discord, asyncio
import lavalink
from discord.ext import commands
from Config.components import Music as msc, MusicActions, LavalinkVoiceClient
from Config.core import Viola

url_rx = re.compile(r'https?://(?:www\.)?.+')

class Music(commands.Cog):
    def __init__(self, bot: Viola):
        self.seconds = 0
        self.ed = False
        self.bot = bot
        self.player = None
        self.bot.loop.create_task(self.genseconds())
        self.bot.loop.create_task(self.some_shit())
        self.bot.loop.create_task(self.connectnodes())
        lavalink.add_event_hook(self.track_hook)
    async def connectnodes(self):
        if not hasattr(self.bot, 'lavalink'):
            self.bot.lavalink = lavalink.Client(self.bot.user.id)
        self.bot.lavalink.node_manager.add_node(host='lavalink.cloudblue.ml', port=1555, password='lava', region='eu', resume_key='default-node', resume_timeout=60, name=None, reconnect_attempts=3)
    async def genseconds(self):
        while True:
            try:
                if self.player.is_playing and not self.player.paused:
                    self.seconds += 1
                await asyncio.sleep(1)
            except AttributeError:
                await asyncio.sleep(1)
    async def some_shit(self):
        while True:
            self.ed = False
            await asyncio.sleep(7)
    async def cog_before_invoke(self, ctx):
        if ctx.command.name == 'node':
            return
        guild_check = ctx.guild is not None
        if guild_check:
            await self.ensure_voice(ctx)
        return guild_check
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)
    async def ensure_voice(self, ctx: commands.Context):
        while True:
            try:
                self.player: lavalink.DefaultPlayer= self.bot.lavalink.player_manager.create(ctx.guild.id, endpoint='eu')
                break
            except lavalink.NodeException:
                print('node exception.')
                await asyncio.sleep(1)
        should_connect = ctx.command.name in ('play', 'p', )
        if not self.player.is_connected:
            if not should_connect:
                raise commands.CommandInvokeError('Not connected.')
            self.player.store('channel', ctx.channel.id)
    async def track_hook(self, event: lavalink.Event):
        if isinstance(event, lavalink.QueueEndEvent):
            player: lavalink.DefaultPlayer = event.player
            guild_id = int(player.guild_id)
            guild = self.bot.get_guild(guild_id)
            try:
                await guild.voice_client.disconnect(force=True)
            except AttributeError:
                pass
            embed = discord.Embed(color=discord.Color.green())
            embed.title = 'Музыка больше не проигрывается.'
            embed.description = '`Я больше не проигрываю музыку, так-как песен в очереди больше нет.`'
            try:
                embed.set_footer(text=f'{guild.name}', icon_url=f'{guild.icon.url}')
            except Exception:
                embed.set_footer(text=f'{guild.name}', icon_url=f'{self.bot.user.avatar.url}')
            mess = player.fetch('mess')
            await mess.edit(embed=embed, view=None)
            player.delete('mess')
        elif isinstance(event, lavalink.TrackEndEvent):
            self.seconds = 0
            player: lavalink.DefaultPlayer = event.player
            if not player.repeat:
                player.store('ended', event.track)
        elif isinstance(event, lavalink.events.PlayerUpdateEvent):
            if not self.ed and self.player.is_playing:
                self.ed = True
                def thumb(ident: str):
                    return f'https://img.youtube.com/vi/{ident}/0.jpg'
                seconds = self.seconds
                player: lavalink.DefaultPlayer = event.player
                embed = discord.Embed(color=discord.Color.blurple())
                try:
                    tim = self.bot.format_time(player.current.duration / 1000)
                except AttributeError:
                    pass
                try:
                    percents = (int(seconds) / (player.current.duration / 1000)) * 100
                except (ZeroDivisionError, AttributeError):
                    percents = 0
                percents = round(percents, 1)
                name = player.current.title
                url = player.current.uri
                if player.repeat:
                    repeat = '\nРежим повтора включен. 🔁'
                else:
                    repeat = ''
                progress = '**[**' + ('🟩' * int(percents // 10)) + ('🟥' * (10 - int(percents // 10))) + f'**]** `{self.bot.format_time(seconds)}`'
                embed.description = f'**Сейчас играет:**\n[**{name}**]({url})\n`Длительность:` **[{tim}]**\n`Запросил:` **{self.bot.get_user(player.current.requester)}**\n\n{progress}{repeat}' #\nNode: `{player.node}`
                embed.set_thumbnail(url=thumb(player.current.identifier))
                while True:
                    try:
                        await mess.edit(embed=embed)
                        break
                    except (AttributeError, UnboundLocalError):
                        mess = player.fetch('mess')
                        await asyncio.sleep(0.3)
                    except discord.errors.NotFound:
                        break
        elif isinstance(event, lavalink.events.TrackStuckEvent):
            print('stuck!')
            print(event.threshold)
        elif isinstance(event, lavalink.events.TrackExceptionEvent):
            print(event.exception)
            print('exception!')
    
    @commands.command(aliases=['p'])
    async def play(self, ctx: commands.Context, *, Трек):
        # await ctx.channel.send('`Музыка временно отключена.`')
        # return
        query: str = Трек
        async with ctx.message.channel.typing():
            playing = False
            added = False
            player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.get(ctx.guild.id)
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.channel.send(embed=discord.Embed(color=discord.Color.red(), description='Присоединитесь к голосовому каналу {0} чтобы ставить музыку.'.format(f'<#{player.channel_id}>' if player.channel_id else ''), title='Ошибка.'))
                return
            permissions = ctx.author.voice.channel.permissions_for(ctx.me)
            if not permissions.connect or not permissions.speak:
                await ctx.channel.send(embed=discord.Embed(color=discord.Color.red(), description='Мне нужны права `Говорить` и `Подключаться` к каналу.', title='Ошибка.'))
                return
            if player.is_connected:
                if int(player.channel_id) != ctx.author.voice.channel.id:
                    await ctx.channel.send(embed=discord.Embed(color=discord.Color.red(), description=f'Подключитесь к каналу <#{player.channel_id}> чтобы проигрывать треки.', title='Ошибка.'))
                    return
            await player.set_volume(vol=65)
            query = query.strip('<>')

            if not url_rx.match(query):
                query = f'ytsearch:{query}'

            results = await player.node.get_tracks(query)
            if not results or not results['tracks']:
                return await ctx.message.reply(content='`Совпадений не найдено.`')
            res_tracks = []
            for i in results['tracks']:
                res_tracks.append(i)
            def thumb(ident: str):
                return f'https://img.youtube.com/vi/{ident}/0.jpg'
            if len(res_tracks) == 1:
                track = lavalink.AudioTrack(res_tracks[0], ctx.author.id, recommended=True)
                player.add(requester=ctx.author.id, track=track)
                if not player.is_playing:
                    try:
                        a = await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient, self_deaf=True)
                        player.store('client', a)
                    except discord.errors.ClientException:
                        pass
                    await player.play()
                    embed = discord.Embed(color=discord.Color.blurple())
                    embed.title = 'Трек выбран.'
                    tim = '0:00'
                    embed.description = f'**Сейчас играет:**\n[**{res_tracks[0]["info"]["title"]}**]({res_tracks[0]["info"]["uri"]})\n`Длительность:` [**{tim}**]\n`Запросил:` **{self.bot.get_user(player.current.requester)}**\n\n**[**🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥**]**'
                    embed.set_thumbnail(url=thumb(player.current.identifier))
                    mess: discord.Message = player.fetch('mess')
                    player.store('mess', await ctx.channel.send(embed=embed, view=MusicActions(bot=self.bot, ctx=ctx, player=player)))
                    playing = True
                else:
                    embed = discord.Embed(color=discord.Color.blurple())
                    embed.title = 'Трек Добавлен.'
                    embed.description = f'**Добавлено в очередь:**\n[**{res_tracks[0]["info"]["title"]}**]({res_tracks[0]["info"]["uri"]})'
                    embed.set_thumbnail(url=thumb(res_tracks[0]["info"]['identifier']))
                    mess = await ctx.channel.send(embed=embed)
                    added = True
            if not playing and not added:
                if results['loadType'] == 'PLAYLIST_LOADED':
                    tracks = results['tracks']
                    for track in tracks:
                        player.add(requester=ctx.author.id, track=track)
                    try:
                        a = await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient, self_deaf=True)
                        player.store('client', a)
                    except discord.errors.ClientException:
                        pass
                    embed = discord.Embed(color=discord.Color.blurple())
                    embed.title = f'Плейлист из {len(tracks)} треков добавлен в очередь.'
                    embed.description = f'**{results["playlistInfo"]["name"]}** - {len(tracks)} Треков.'
                    if not player.is_playing:
                        await player.play()
                    mess = await ctx.channel.send(embed=embed)
                    await mess.edit(view=MusicActions(bot=self.bot, ctx=ctx, player=player, actualmsg=mess))
                else:
                    embed = discord.Embed(color=discord.Color.blurple())
                    embed.description = 'Выберите трек из списка **ниже**:\n`У вас есть 60 секунд. Затем бот перестанет реагировать на это сообщение.`'
                    await ctx.channel.send(content=f'`✨Найдено {len(res_tracks)} Совпадений с вашим запросом.`', embed=embed, view=msc(bot=self.bot, results=res_tracks, player=player, ctx=ctx))

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))