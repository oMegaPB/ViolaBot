import re, contextlib
import traceback, datetime
import discord, asyncio
import lavalink, random
from discord import app_commands
from discord.ext import commands
from Config.components import Music as msc, MusicActions, LavalinkVoiceClient
from Config.core import Viola

url_rx = re.compile(r'https?://(?:www\.)?.+')

class Music(commands.Cog):
    def __init__(self, bot: Viola):
        self.bot = bot
        self.rate_limit = False
    async def cog_load(self):
        lavalink.add_event_hook(self.track_hook)
        self.bot.lavalink = lavalink.Client(self.bot.user.id)
        self.bot.lavalink.node_manager.add_node(host='lavalink.cloudblue.ml', port=1555, password='lava', region='eu', resume_key='default-node', resume_timeout=60, name=None, reconnect_attempts=3)
    async def track_hook(self, event: lavalink.Event):
        if isinstance(event, lavalink.QueueEndEvent):
            event.player.queue_end = True
            guild_id = int(event.player.guild_id)
            guild = self.bot.get_guild(guild_id)
            with contextlib.suppress(AttributeError):
                await guild.voice_client.disconnect(force=True)
            embed = discord.Embed(color=discord.Color.green())
            embed.title = 'Музыка больше не проигрывается.'
            embed.description = '`Я больше не проигрываю музыку, так-как песен в очереди больше нет.`'
            try:
                embed.set_footer(text=f'{guild.name}', icon_url=f'{guild.icon.url}')
            except Exception:
                embed.set_footer(text=f'{guild.name}', icon_url=f'{self.bot.user.avatar.url}')
            event.player.ended = []
            await event.player.message.edit(embed=embed, view=None)
        elif isinstance(event, lavalink.TrackStartEvent):
            event.player.seconds = 0
            if not event.player.tasks:
                async def _update_player():
                    while True:
                        if event.player.is_connected and not event.player.paused:
                            event.player.seconds += 1
                        await asyncio.sleep(1)
                async def _cooldown():
                    while True:
                        self.rate_limit = False
                        await asyncio.sleep(6 + random.randint([-1, 1]))
                event.player.tasks = True
                self.bot.loop.create_task(_cooldown())
                self.bot.loop.create_task(_update_player())
        elif isinstance(event, lavalink.TrackEndEvent):
            event.player.seconds = 0
            event.player.ended.append(event.track)
        elif isinstance(event, lavalink.WebSocketClosedEvent):
            if event.player.is_connected:
                return
            guild = self.bot.get_guild(int(event.player.guild_id))
            embed = discord.Embed(color=discord.Color.green())
            a: discord.Member = event.player.fetch(key=int(event.player.guild_id))
            if a is not None:
                event.player.delete(key=guild.id)
                embed.description = f'`Я покинула голосовой канал.`'
                try:
                    embed.set_footer(text=f'Действие запрошено {a}.', icon_url=f'{a.avatar.url}')
                except Exception:
                    embed.set_footer(text=f'Действие запрошено {a}.')
                embed.color = discord.Color.blurple()
            else:
                embed.description = '`Музыка больше не проигрывается так как меня отключили из голосового канала.`'
                try:
                    embed.set_footer(text=f'{guild.name}', icon_url=f'{guild.icon.url}')
                except Exception:
                    embed.set_footer(text=f'{guild.name}', icon_url=f'{self.bot.user.avatar.url}')
            with contextlib.suppress(AttributeError):
                event.player.ended = []
                if not event.player.queue_end:
                    return await event.player.message.edit(embed=embed, view=None)
        elif isinstance(event, lavalink.events.PlayerUpdateEvent):
            if not self.rate_limit:
                self.rate_limit = True
                guild = self.bot.get_guild(int(event.player.guild_id))
                emojis = {
                    'play': '<:play:1013382795227308082>',
                    'start0': '<:start0:1013382791771209848>',
                    'start1': '<:start1:1013382793365045260>',
                    'middle0': '<:middle0:1013384036598698024>',
                    'middle1': '<:middle1:1013384040809766943>',
                    'end0': '<:end0:1013384039257882676>',
                    'end1': '<:end1:1013384037982806056>',
                    }
                def thumb(ident: str):
                    return f'https://img.youtube.com/vi/{ident}/0.jpg'
                embed = discord.Embed(color=discord.Color.blurple())
                try:
                    embed.set_footer(text=f'{guild.name}', icon_url=f'{guild.icon.url}')
                except Exception:
                    embed.set_footer(text=f'{guild.name}', icon_url=f'{self.bot.user.avatar.url}')
                with contextlib.suppress(AttributeError):
                    tim = self.bot.format_time(event.player.current.duration / 1000)
                try:
                    percents = (event.player.seconds / (event.player.current.duration / 1000)) * 100
                except (ZeroDivisionError, AttributeError):
                    percents = 0
                percents = round(percents, 1)
                with contextlib.suppress(AttributeError):
                    name = event.player.current.title
                    url = event.player.current.uri
                    if event.player.repeat:
                        repeat = '\n🔁 **Режим повтора включен.**'
                    else:
                        repeat = ''
                    if event.player.shuffle:
                        repeat += '\n🔀 **Режим перемешивания включен.**'
                    progressbar = ('🟩' * int(percents // 10)) + ('🟥' * (10 - int(percents // 10)))
                    emojibar = f'{emojis["play"]} '
                    for i, j in enumerate(progressbar):
                        if i == 0 or i == 9:
                            if j == '🟩' and i == 0:
                                emojibar+= emojis['start1']
                            elif j == '🟥' and i == 0:
                                emojibar+= emojis['start0']
                            elif j == '🟩' and i == 9:
                                emojibar+= emojis['end1']
                            elif j == '🟥' and i == 9:
                                emojibar+= emojis['end0']
                        else:
                            if j == '🟩':
                                emojibar+= emojis['middle1']
                            else:
                                emojibar+= emojis['middle0']
                    if event.player.volume > 300:
                        event.player.volume = 60
                    vol = f'\n`Громкость:` **{event.player.volume}%**' if event.player.volume != 60 else ''
                    emojibar += f' `{self.bot.format_time(event.player.seconds)} / {tim}`'
                    embed.description = f'**Сейчас играет:**\n[**{name}**]({url})\n`Длительность:` **[{tim}]**\n`Запросил:` **{guild.get_member(int(event.player.current.requester))}**{vol}\n\n{emojibar}{repeat}' #\nNode: `{player.node}`
                    embed.set_thumbnail(url=thumb(event.player.current.identifier))
                    with contextlib.suppress(AttributeError, UnboundLocalError, discord.NotFound):
                        await event.player.message.edit(embed=embed)
        elif isinstance(event, lavalink.TrackStuckEvent):
            print('stuck!')
            print(event.threshold)
        elif isinstance(event, lavalink.TrackExceptionEvent):
            print(event.exception)
            print('exception!')
    
    @app_commands.command(description="Поставьте вашу любимую песню.")
    async def play(self, interaction: discord.Interaction, track: str) -> None:
        try:
            await interaction.response.defer(thinking=True)
            if not interaction.guild:
                return await interaction.followup.send('`Я не умею играть музыку тут(`')
            player = self.bot.lavalink.player_manager.get(interaction.guild.id)
            if not player:
                while True:
                    try:
                        player: lavalink.DefaultPlayer = self.bot.lavalink.player_manager.create(interaction.guild.id, endpoint='eu')
                        player.tasks = False
                        player.ended = []
                        player.queue_end = False
                        break
                    except (lavalink.NodeException, Exception):
                        print('node exception.')
                        await asyncio.sleep(3)
            if not interaction.user.voice or not interaction.user.voice.channel:
                return await interaction.followup.send(embed=discord.Embed(color=discord.Color.red(), description='Присоединитесь к голосовому каналу {0} чтобы ставить музыку.'.format(f'<#{player.channel_id}>' if player.channel_id else ''), title='Ошибка.'))
            permissions = interaction.user.voice.channel.permissions_for(interaction.guild.get_member(self.bot.user.id))
            if not permissions.connect or not permissions.speak:
                return await interaction.followup.send(embed=discord.Embed(color=discord.Color.red(), description='Мне нужны права `Говорить` и `Подключаться` к каналу.', title='Ошибка.'))
            if player.is_connected:
                if int(player.channel_id) != interaction.user.voice.channel.id:
                    return await interaction.followup.send(embed=discord.Embed(color=discord.Color.red(), description=f'Подключитесь к каналу <#{player.channel_id}> чтобы проигрывать треки.', title='Ошибка.'))
            await player.set_volume(vol=60)
            query = track.strip('<>')

            if not url_rx.match(query):
                query = f'ytsearch:{query}'

            results = await player.node.get_tracks(query)
            if not results or not results['tracks']:
                return await interaction.followup.send(content='`Совпадений не найдено...`')
            res_tracks = [i for i in results['tracks']]
            def thumb(ident: str):
                return f'https://img.youtube.com/vi/{ident}/0.jpg'
            if len(res_tracks) == 1:
                track = lavalink.AudioTrack(res_tracks[0], interaction.user.id, recommended=True)
                player.add(requester=interaction.user.id, track=track)
                if not player.is_playing:
                    with contextlib.suppress(discord.ClientException):
                        player.client = await interaction.user.voice.channel.connect(cls=LavalinkVoiceClient, self_deaf=True)
                    await player.play()
                    embed = discord.Embed(color=discord.Color.blurple())
                    embed.title = 'Трек выбран.'
                    tim = '0:00'
                    embed.description = f'**Сейчас играет:**\n[**{res_tracks[0]["info"]["title"]}**]({res_tracks[0]["info"]["uri"]})\n`Длительность:` [**{tim}**]\n`Запросил:` **{self.bot.get_user(player.current.requester)}**\n\n**[**🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥**]**'
                    embed.set_thumbnail(url=thumb(player.current.identifier))
                    view = MusicActions(bot=self.bot, player=player)
                    view.message = await interaction.followup.send(embed=embed, view=view)
                    player.message = view.message
                    return
                else:
                    embed = discord.Embed(color=discord.Color.blurple())
                    embed.title = 'Трек Добавлен.'
                    embed.description = f'**Добавлено в очередь:**\n[**{res_tracks[0]["info"]["title"]}**]({res_tracks[0]["info"]["uri"]})'
                    embed.set_thumbnail(url=thumb(res_tracks[0]["info"]['identifier']))
                    return await interaction.followup.send(embed=embed)
            if results['loadType'] == 'PLAYLIST_LOADED':
                tracks = results['tracks']
                for track in tracks:
                    player.add(requester=interaction.user.id, track=track)
                with contextlib.suppress(discord.ClientException):
                    player.client = await interaction.user.voice.channel.connect(cls=LavalinkVoiceClient, self_deaf=True)
                embed = discord.Embed(color=discord.Color.blurple())
                embed.title = f'Плейлист из {len(tracks)} треков добавлен в очередь.'
                embed.description = f'**{results["playlistInfo"]["name"]}** - {len(tracks)} Треков.'
                if not player.is_playing:
                    await player.play()
                    view = MusicActions(bot=self.bot, player=player)
                    view.message = await interaction.followup.send(embed=embed, view=view)
                    player.message = view.message
                else:
                    await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(color=discord.Color.blurple())
                embed.description = 'Выберите нужный вам трек из списка песен **ниже**:\n`На выбор трека у вас есть 60 секунд.`<:NepSmug:986661966917546024>'
                used, options = [], []
                for x in res_tracks:
                    if x['info']['author'] in used:
                        continue
                    used.append(x['info']['author'])
                    options.append(discord.SelectOption(label=f"{x['info']['author']}",emoji="🎵",description=f"{x['info']['title']}"))
                view = msc(options=options, player=player, ctx=interaction, results=res_tracks)
                view.message = await interaction.followup.send(content=f'`✨Найдено {len(options)} Совпадений с вашим запросом.`', embed=embed, view=view)
        except Exception:
            print(traceback.format_exc())
async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))