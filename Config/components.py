import json
import traceback, datetime
import discord, asyncio, random
from discord.ext import commands
from typing import List
import emoji, lavalink
from youtube_transcript_api import YouTubeTranscriptApi
import youtube_transcript_api

# Reactions -----------------------------------------------------------------------------------------------------------
class ReactionsCallback(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Добавить параметр.",emoji="👌",description="Добавить параметр выдачи роли по реакции."),
            discord.SelectOption(label="Удалить параметр.",emoji="✨",description="Удалить параметр выдачи роли по реакции."),
            discord.SelectOption(label="Просмотр параметров.",emoji="🎭",description="Просмотреть все параметры на этом сервере.")
            ]
        super().__init__(placeholder="Выберите опцию.", max_values=1, min_values=1, options=options)
    def embed(self, description, interaction: discord.Interaction, format='Normal'):
        embed = discord.Embed(description=f'**{description}**')
        if format == 'Error':
            embed.title = 'Ошибка'
            embed.color = discord.Color.red()
        elif format == 'Normal':
            embed.title = 'Роли по реакции.'
            embed.color = discord.Color.random()
        # embed.set_footer(text=f'{interaction.guild.name}', icon_url=f'{interaction.guild.icon}')
        return embed
    async def callback(self, interaction: discord.Interaction):
        def check(m: discord.Message):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        if self.values[0] == 'Добавить параметр.':
            args = []
            try:
                # ------------------------------------------------------------------------------------------
                await interaction.response.defer()
                async with interaction.channel.typing():
                    mess = await interaction.channel.send(embed=self.embed('Введите id канала:', interaction), view=CloseButton())
                try:
                    msg: discord.Message = await interaction.client.wait_for('message', timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    return
                try:
                    await interaction.channel.fetch_message(mess.id)
                except discord.errors.NotFound:
                    return
                await msg.delete()
                channel = interaction.client.get_channel(int(msg.content))
                if channel is None or channel.guild.id != interaction.guild_id or (channel.type is not discord.ChannelType.text):
                    await mess.edit(embed=self.embed('Канал не найден среди текстовых каналов этого сервера.', interaction, format='Error'))
                    return
                args.append(channel.id)
                # ------------------------------------------------------------------------------------------
                mess = await mess.edit(embed=self.embed(f'`Канал:` <#{channel.id}>\n\n**Введите id Сообщения:**', interaction), view=CloseButton())
                try:    
                    msg = await interaction.client.wait_for('message', timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    return
                try:
                    await interaction.channel.fetch_message(mess.id)
                except discord.errors.NotFound:
                    return
                await msg.delete()
                try:
                    message = await interaction.client.get_channel(int(args[0])).fetch_message(int(msg.content))
                except discord.errors.NotFound:
                    await mess.edit(embed=self.embed('Сообщение не найдено.', interaction, format='Error'))
                    return
                args.append(message.id)
                # ------------------------------------------------------------------------------------------
                mess = await mess.edit(embed=self.embed(f'`Канал:` <#{channel.id}>\n`Сообщение:` [[{message.id}]]({message.jump_url})\n\n**Упомяните роль или отправьте ее id:**', interaction), view=CloseButton())
                try:    
                    msg = await interaction.client.wait_for('message', timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    return
                try:
                    await interaction.channel.fetch_message(mess.id)
                except discord.errors.NotFound:
                    return
                await msg.delete()
                role = discord.utils.get(interaction.guild.roles, id=int(msg.content.replace('<@&', '').replace('>', '')))
                if role is not None:
                    args.append(role.id)
                else:
                    await mess.edit(content='', embed=self.embed('Роль не найдена', interaction, format='Error'))
                    return
                try:
                    await interaction.user.add_roles(role)
                    await asyncio.sleep(0.5)
                    await interaction.user.remove_roles(role)
                except discord.errors.Forbidden:
                    await mess.edit(embed=self.embed('У бота нет прав на выдачу этой роли.', interaction, format='Error'))
                    return
                # ------------------------------------------------------------------------------------------
                added = False
                mess = await mess.edit(embed=self.embed(f'`Канал:` <#{channel.id}>\n`Сообщение:` [[{message.id}]]({message.jump_url})\n`Роль:` <@&{role.id}>\n\n**Отправьте нужную вам реакцию в чат:**', interaction), view=CloseButton())
                try:    
                    msg = await interaction.client.wait_for('message', timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    return
                try:
                    await interaction.channel.fetch_message(mess.id)
                except discord.errors.NotFound:
                    return
                if emoji.emoji_count(msg.content) == 1:
                    reaction = msg.content
                    await message.add_reaction(str(msg.content))
                    added = True
                    raw_reaction = msg.content
                elif emoji.emoji_count(msg.content) > 1:
                    await mess.edit(embed=self.embed('Неверный формат.', interaction, format='Error'))
                    await msg.delete()
                    return
                else:
                    if msg.content.count(':') == 2 and msg.content.count('<') == 1 and msg.content.count('>') == 1:
                        reaction = msg.content[:len(msg.content)-20]
                        if msg.content.count('<a:') == 1:
                            reaction = reaction[3:]
                        else:
                            reaction = reaction[2:]
                        raw_reaction = msg.content
                        for x in interaction.client.emojis:
                            if str(raw_reaction) == str(x):
                                await message.add_reaction(x)
                                added = True
                    else:
                        await mess.edit(embed=self.embed('Неверный формат.', interaction, format='Error'))
                        await msg.delete()
                        return
                await msg.delete()
                args.append(reaction)
                # ------------------------------------------------------------------------------------------
                res = await interaction.client.bd.fetch({'guildid': interaction.guild.id, 'channel_id': args[0], 'message_id': args[1], 'reaction': args[3], 'role_id': args[2]}, category='reactroles')
                while True:
                    id = random.randint(100000, 999999)
                    res = await interaction.client.bd.fetch({'uniqid': id}, category='reactroles')
                    if not res.status:
                        break
                if not res.status:
                    res = await interaction.client.bd.add(
                        {'guildid': interaction.guild.id, 'channel_id': args[0], 'message_id': args[1], 'reaction': args[3], 'role_id': args[2], 'uniqid': id},
                        category='reactroles'
                    )
                else:
                    await mess.edit(embed=self.embed('Такой параметр уже существует.', interaction, format='Error'))
                    return
                if not added:
                    await interaction.channel.send('`Бот не знает этой реакции. Вам нужно поставить ее самому.`', delete_after=10.0)
                await mess.edit(embed=discord.Embed(title='Роли за реакцию.', description=f'Параметр добавлен.\nКанал: <#{channel.id}>\nid сообщения: [**{message.id}**]({message.jump_url})\nРеакция: {raw_reaction}\nРоль: <@&{role.id}>\nID: {id}', color=discord.Color.green()), view=None)
            except (asyncio.TimeoutError, Exception):
                try:
                    await mess.delete()
                except Exception:
                    return
        elif self.values[0] == 'Просмотр параметров.':
            async with interaction.channel.typing():
                await interaction.response.defer()
                res = await interaction.client.bd.fetch({'guildid': interaction.guild.id}, mode='all', category='reactroles')
                content = ''
                count = 0
                if res.status:
                    for y in res.value:
                        channel = interaction.client.get_channel(int(y['channel_id']))
                        try:
                            message = await channel.fetch_message(int(y['message_id']))
                        except (discord.errors.NotFound, Exception):
                            await interaction.client.bd.remove(y, category='reactroles')
                            continue
                        count += 1
                        content += f'**{count}.**\n`Канал:` <#{channel.id}>\n`Сообщение:` [**[{message.id}]**]({message.jump_url})\n`Реакция:` {y["reaction"]}\n`Роль:` <@&{y["role_id"]}>\n`ID:` [{y["uniqid"]}]\n'
                    if content == '':
                        content = 'Параметров для этого сервера не найдено.'
                    embed = discord.Embed(title='Все параметры связанные с этми сервером:', description=content)
                    embed.color = 0x00ffff
                    mess = await interaction.channel.send(embed=embed)
                    return
                else:
                    await interaction.channel.send(embed=discord.Embed(title='Все параметры связанные с этим сервером:',description='Параметров для этого сервера не найдено.', color = 0x00ffff))
                    return
        elif self.values[0] == 'Удалить параметр.':
            async with interaction.channel.typing():
                await interaction.response.defer()
                res = await interaction.client.bd.fetch({'guildid': interaction.guild.id}, mode='all', category='reactroles')
                if not res.status:
                    await interaction.channel.send(embed=self.embed(f'Параметров для этого сервера не найдено.', interaction, format='Error'))
                    return
                mess = await interaction.channel.send(embed=self.embed(f'Отправьте в чат id параметра:', interaction), view=CloseButton())
                try:
                    try:
                        msg = await interaction.client.wait_for('message', timeout=60.0, check=check)
                        try:
                            await interaction.channel.fetch_message(mess.id)
                        except discord.errors.NotFound:
                            return
                        await msg.delete()
                    except asyncio.TimeoutError:
                        try:
                            await mess.delete()
                            return
                        except discord.errors.NotFound:
                            return
                    res = await interaction.client.bd.fetch({'uniqid': int(msg.content)}, category='reactroles')
                    if res.status:
                        await interaction.client.bd.remove(res.value, category='reactroles')
                        await mess.edit(embed=self.embed(f'Параметр успешно удален.', interaction), view=None)
                        return
                    else:
                        await mess.edit(embed=self.embed(f'Параметр не найден.', interaction, format='Error'), view=None)
                        return
                except Exception as e:
                    print(traceback.format_exc())
class CloseButton(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
    @discord.ui.button(label="❌Выход", style=discord.ButtonStyle.red)
    async def close(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
class Reactions(discord.ui.View):
    def __init__(self, *, timeout=None, ctx: commands.Context):
        self.ctx = ctx
        super().__init__(timeout=timeout)
        self.add_item(ReactionsCallback())
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(embed=discord.Embed(title='Error', description='Вы не можете взаимодействовать с этим сообщением, т.к его вызвал другой человек.', color=discord.Color.red()), ephemeral=True)
            return False
        return True
# Logs -----------------------------------------------------------------------------------------------------------
class LogsCallback(discord.ui.Select):
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self.ctx = ctx
        options=[
            discord.SelectOption(label="Добавить систему логов.",emoji="🗒️",description="Добавить систему логирования событий сервера."),
            discord.SelectOption(label="Удалить систему логов.",emoji="📎",description="Удалить систему логирования событий сервера."),
            discord.SelectOption(label="Состояние системы.",emoji="📡",description="Просмотр состояния системы.")
            ]
        super().__init__(placeholder="Выберите опцию.", max_values=1, min_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.values[0] == 'Добавить систему логов.':
            res = await self.bot.bd.fetch({'guildid': self.ctx.guild.id}, category='logs')
            if not res.status:
                def check(m: discord.Message):
                    return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
                if len(self.ctx.guild.text_channels) > 25:
                    await interaction.followup.send('`Отправьте в чат id текстового канала:`', ephemeral=True)
                    try:    
                        msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                    except asyncio.TimeoutError:
                        return
                    await msg.delete()
                    channel = self.bot.get_channel(int(msg.content))
                    if channel is None or channel not in self.ctx.guild.text_channels:
                        await interaction.followup.send('`Канал не найден среди текстовых каналов этого сервера.`', ephemeral=True)
                        return
                    await self.bot.bd.add({'guildid': interaction.guild.id, 'channel_id': int(msg.content), 'date': datetime.datetime.now().timestamp(), 'memberid': interaction.user.id}, category='logs')
                    embed = discord.Embed(color=discord.Color.green())
                    embed.title = 'Успешно.'
                    embed.description = f'Система логирования добавлена. Канал: <#{channel.id}>'
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(color=discord.Color.green())
                    embed.title = 'Логирование.'
                    embed.description = 'Выберите канал для логирования:'
                    await interaction.followup.send(embed=embed, view=LogsHelper(bot=self.bot, ctx=self.ctx), ephemeral=True)
            else:
                embed = discord.Embed(color=discord.Color.red())
                embed.title = 'Ошибка.'
                embed.description = f'Система логов уже активна.\nКанал: {self.bot.get_channel(res.value["channel_id"]).mention}'
                await interaction.followup.send(embed=embed, ephemeral=True)
        elif self.values[0] == 'Удалить систему логов.':
            res = await self.bot.bd.fetch({'guildid': self.ctx.guild.id}, category='logs')
            if res.status:
                embed = discord.Embed(color=discord.Color.red())
                embed.title = 'Внимание!'
                embed.description = 'Система Логирования будет удалена.\nПродолжить?'
                await interaction.followup.send(embed=embed, view=ConfirmRemove(bot=self.bot, ctx=self.ctx))
            else:
                embed = discord.Embed(color=discord.Color.green())
                embed.title = 'Логирование.'
                embed.description = '`Система Логирования не найдена.`'
                await interaction.followup.send(embed=embed, ephemeral=True)
        elif self.values[0] == 'Состояние системы.':
            res = await self.bot.bd.fetch({'guildid': interaction.guild.id}, category='logs')
            if res.status:
                embed = discord.Embed(color=discord.Color.green())
                embed.title='Логирование.'
                description = f'`Канал:` {self.bot.get_channel(int(res.value["channel_id"])).mention}\n'
                try:
                    user = self.bot.get_user(int(res.value["memberid"]))
                    description += f'`Добавил систему:` {user.name} ({user.mention})\n'
                except BaseException:
                    description += f'`Добавил систему:` Unknown\n'
                try:
                    description += f'`Дата:` <t:{int(res.value["date"])}:R>\n'
                except BaseException:
                    description += f'`Дата:` Unknown'
                embed.description = description
                try:
                    embed.set_footer(text=f'{interaction.guild.name}', icon_url=f'{interaction.guild.icon.url}')
                except Exception:
                    embed.set_footer(text=f'{interaction.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(color=discord.Color.green())
                embed.title='Логирование.'
                embed.description = f'`Система логов сервера не найдена`'
                await interaction.followup.send(embed=embed, ephemeral=True)
class LogsChannels(discord.ui.Select):
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self.ctx = ctx
        options=[discord.SelectOption(label=f"{x.id}",emoji="✉️",description=f"{x}") for x in self.ctx.guild.channels if x.type is discord.ChannelType.text]
        super().__init__(placeholder="Выберите Канал.", max_values=1, min_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        res = await self.bot.bd.fetch({'guildid': self.ctx.guild.id}, category='logs')
        channel = self.bot.get_channel(int(self.values[0]))
        if not res.status:
            await self.bot.bd.add({'guildid': interaction.guild.id, 'channel_id': int(self.values[0]), 'date': datetime.datetime.now().timestamp(), 'memberid': interaction.user.id}, category='logs')
            embed = discord.Embed(color=discord.Color.green())
            embed.title = 'Успешно.'
            embed.description = f'Система логирования добавлена. Канал: <#{channel.id}>'
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send('`Что то пошло не так...`', ephemeral=True)
class Logs(discord.ui.View):
    def __init__(self, *, timeout=120.0, bot: commands.Bot, ctx: commands.Context):
        super().__init__(timeout=timeout)
        self.add_item(LogsCallback(bot=bot, ctx=ctx))
class LogsHelper(discord.ui.View):
    def __init__(self, *, timeout=120.0, bot: commands.Bot = None, ctx: commands.Context):
        super().__init__(timeout=timeout)
        self.add_item(LogsChannels(bot=bot, ctx=ctx))
class ConfirmRemove(discord.ui.View):
    def __init__(self, *, timeout=60.0, bot: commands.Bot, ctx: commands.Context):
        super().__init__(timeout=timeout)
        self.bot=bot
        self.ctx=ctx
    @discord.ui.button(label="❌Продолжить", style=discord.ButtonStyle.red)
    async def remove(self, interaction:discord.Interaction, button: discord.ui.Button):
        embed = ViolaEmbed(ctx=self.ctx)
        embed.description = 'Система логирования была отключена.'
        await interaction.message.edit(embed=embed, view=None)
        try:
            channel = await self.bot.getLogChannel(self.ctx.guild.id)
            embed = discord.Embed(color=discord.Color.green())
            embed.title = 'Логирование.'
            embed.description = f'Система логирования отключена пользователем {interaction.user.mention}!'
            try:
                embed.set_footer(text=f'{self.ctx.guild.name}', icon_url=f'{self.ctx.guild.icon.url}')
            except Exception:
                embed.set_footer(text=f'{self.ctx.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
            await channel.send(embed=embed)
            await self.bot.bd.remove({'guildid': self.ctx.guild.id}, category='logs')
            embed = discord.Embed(color=discord.Color.green())
            embed.title = 'Система логирования.'
            embed.description = 'Функция успешно отключена.'
            await interaction.followup.send(embed=embed, ephemeral=True)
            self.stop()
        except BaseException:
            return
# Music ----------------------------------------------------------------------------------------------------------------------
class MusicCallback(discord.ui.Select):
    def __init__(self, bot: commands.Bot, results: List[dict], player: lavalink.models.DefaultPlayer, ctx: commands.Context):
        self.bot = bot
        self.player = player
        self.results = results
        self.ctx = ctx
        self.seconds = 0
        self.name = ''
        options = []
        was = []
        self.genseconds = False
        self.update = True
        self.forseek = False
        for x in results:
            if x['info']['author'] in was:
                continue
            was.append(x['info']['author'])
            options.append(discord.SelectOption(label=f"{x['info']['author']}",emoji="🎵",description=f"{x['info']['title']}"))
        super().__init__(placeholder="Выберите Трек.", max_values=1, min_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        def thumb(ident: str):
            return f'https://img.youtube.com/vi/{ident}/0.jpg'
        async def forseek():
            while True:
                a = self.player.fetch('need_to_add')
                if isinstance(a, int):
                    self.player.delete('need_to_add')
                    self.player.store(key='seconds', value=int(self.seconds))
                    self.seconds += 10
                await asyncio.sleep(0.5)
        async def genseconds():
            while True:
                try:
                    if self.seconds * 1000 > self.player.current.duration:
                        self.seconds = 0
                    if not self.player.paused:
                        if self.name != self.player.current.title:
                            self.name = self.player.current.title
                            self.seconds = 0
                        self.seconds += 0.5
                        await asyncio.sleep(0.5)
                    else:
                        await asyncio.sleep(0.5)
                except AttributeError:
                    await asyncio.sleep(0.5)
        if not self.genseconds:
            self.bot.loop.create_task(genseconds())
            self.genseconds = True
        if not self.forseek:
            self.bot.loop.create_task(forseek())
            self.forseek = True
        await interaction.response.defer()
        for x in self.results:
            if x['info']['author'] == self.values[0]:
                track = lavalink.models.AudioTrack(x, interaction.user.id, recommended=True)
                self.player.add(requester=interaction.user.id, track=track)
                if not self.player.is_playing:
                    try:
                        a = await self.ctx.author.voice.channel.connect(cls=LavalinkVoiceClient, self_deaf=True)
                        self.player.store('client', a)
                        self.player.store('mess', interaction.message)
                    except discord.errors.ClientException as e:
                        pass
                    await self.player.play()
                    embed = discord.Embed(color=discord.Color.blurple())
                    embed.title = 'Трек выбран.'
                    tim = self.bot.format_time(int(str(self.player.current.duration)[:3]))
                    embed.description = f'**Сейчас играет:**\n[**{x["info"]["title"]}**]({x["info"]["uri"]})\n`Длительность:` [**{tim}**]\n`Запросил:` **{self.bot.get_user(self.player.current.requester)}**\n\n**[**🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥**]**'
                    embed.set_thumbnail(url=thumb(self.player.current.identifier))
                    await interaction.message.edit(content='', embed=embed, view=MusicActions(bot=self.bot, ctx=self.ctx, player=self.player))
                    return
                else:
                    embed = discord.Embed(color=discord.Color.blurple())
                    embed.title = 'Трек Добавлен в очередь.'
                    description = ''
                    description += f'**Очередь:**\n'
                    count = 0
                    for j in self.player.queue:
                        count += 1
                        description += f'`{count}.` [**{j.title}**]({j.uri})\n`Запросил:` **{self.bot.get_user(int(j.requester))}**\n'
                    embed.description = description
                    await interaction.message.edit(content='', embed=embed, view=None)
                    return
class closeButton(discord.ui.Button):
    def __init__(self, label, style):
        super().__init__(label=label, style=style)
    async def callback(self, interaction: discord.Interaction):
        await interaction.message.delete()
class Music(discord.ui.View):
    def __init__(self, *, timeout=60.0, bot: commands.Bot, results: List[dict], player: lavalink.DefaultPlayer, ctx: commands.Context):
        super().__init__(timeout=timeout)
        self.author = ctx.author
        self.player = player
        self.bot = bot
        self.results = results
        self.ctx = ctx
        self.add_item(MusicCallback(bot=self.bot, results=self.results, player=self.player, ctx=self.ctx))
        self.add_item(closeButton(label='❌Выход', style=discord.ButtonStyle.red))
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(embed=discord.Embed(title='Error', description='Вы не можете взаимодействовать с этим сообщением, т.к его вызвал другой человек.', color=discord.Color.red()), ephemeral=True)
            return False
        return True
    async def on_timeout(self):
        self.stop()
class MusicActions(discord.ui.View):
    def __init__(self, *, timeout=None, bot: commands.Bot, player: lavalink.DefaultPlayer, ctx: commands.Context):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.bot = bot
        self.ended = []
        self.edited = 0
        self.mess = None
        self.player = player
        self.paused = False
        self.repeating = False
        self.shuffled = False
        self.bot.loop.create_task(self.update_())
        self.id = self.player.guild_id
    async def update_(self):
        while True:
            if self.mess is None:
                self.mess = self.player.fetch('mess')
            a = self.player.fetch('ended')
            if a is not None:
                self.ended.append(a)
                self.player.delete('ended')
            for x in self.children:
                if isinstance(x, discord.ui.Select):
                    if len(self.ended) > 0 and len(self.ended) != self.edited:
                        self.edited = len(self.ended)
                        options = []
                        used = []
                        y: lavalink.AudioTrack
                        for y in self.ended:
                            if not y.author in used:
                                used.append(y.author)
                                options.append(discord.SelectOption(label=y.author,emoji="🎵",description=y.title))
                        x.options = options
                        x.placeholder = f'Найдено {len(options)} предыдущих треков.'
                        x.disabled = False
                        if self.player.is_playing:
                            await self.mess.edit(view=self)
                elif isinstance(x, discord.ui.Button):
                    if x.label == '⏭️':
                        if len(self.player.queue) > 0 and not self.repeating:
                            if x.disabled:
                                x.disabled = False
                                await self.mess.edit(view=self)
            await asyncio.sleep(0.5)
            if not self.player.is_connected:
                guild = self.bot.get_guild(int(self.id))
                async for x in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_disconnect):
                    a = round(x.created_at.timestamp())
                    b = round((datetime.datetime.utcnow() + datetime.timedelta(hours=3)).timestamp())
                    if b - a > 25 or x.extra.count > 0:
                        embed = discord.Embed(color=discord.Color.green())
                        a: discord.Member = self.player.fetch(key=int(self.player.guild_id))
                        if a is not None:
                            self.player.delete(key=guild.id)
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
                        mess = self.player.fetch('mess')
                        await guild.change_voice_state(channel=None)
                        self.player.channel_id = None
                        client: LavalinkVoiceClient = self.player.fetch('client')
                        try:
                            await client.disconnect(force=True)
                        except AttributeError:
                            pass
                        try:
                            while True:
                                await mess.edit(embed=embed, view=None)
                                self.player.delete('mess')
                                self.ended = []
                                return
                        except AttributeError:
                            mess = self.player.fetch('mess')
                            await asyncio.sleep(0.5)
                        self.ended = []
                        return
    @discord.ui.select(placeholder='Предыдущие треки не найдены.', options=[discord.SelectOption(label="None")], disabled=True)
    async def prevTracks(self, interaction:discord.Interaction, select: discord.ui.Select):
        if not interaction.user.voice or (self.player.is_connected and interaction.user.voice.channel.id != int(self.player.channel_id)):
            return await interaction.response.send_message(f'Подключитесь к каналу <#{self.player.channel_id}> чтобы использовать плеер.', ephemeral=True)
        x: lavalink.AudioTrack
        for x in self.ended:
            if x.author == select.values[0]:
                data = {'track': x.track, 'info': {'identifier': x.identifier, 'isSeekable': x.is_seekable, 'author': x.author, 'length': x.duration, 'isStream': x.stream, 'position': 0, 'sourceName': 'youtube', 'title': x.title, 'uri': x.uri}}
                self.player.add(requester=interaction.user.id, track=data)
        await self.player.skip()
        await interaction.response.defer()
    @discord.ui.button(label="⏹️", style=discord.ButtonStyle.gray)
    async def close(self, interaction:discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or (self.player.is_connected and interaction.user.voice.channel.id != int(self.player.channel_id)):
            return await interaction.response.send_message(f'Подключитесь к каналу <#{self.player.channel_id}> чтобы использовать плеер.', ephemeral=True)
        self.player.store(key=interaction.guild.id, value=interaction.user)
        self.player.queue.clear()
        await self.player.stop()
        await self.ctx.voice_client.disconnect(force=True)
        await interaction.response.defer()
    @discord.ui.button(label="📖", style=discord.ButtonStyle.gray, disabled=False)
    async def lyrics(self, interaction:discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or (self.player.is_connected and interaction.user.voice.channel.id != int(self.player.channel_id)):
            return await interaction.response.send_message(f'Подключитесь к каналу <#{self.player.channel_id}> чтобы использовать плеер.', ephemeral=True)
        await interaction.response.defer()
        embed = discord.Embed(title='Субтитры к видео:', color=discord.Color.blurple())
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id=self.player.current.identifier, languages=('en', 'ru'))
            script = ""
            for text in transcript:
                t = text["text"]
                if t != '[Music]':
                    script += t + " "
            embed.description = script
            await interaction.followup.send(embed=embed, ephemeral=True)
        except youtube_transcript_api.CouldNotRetrieveTranscript as e:
            embed.description= f'Ответ от youtube-api:\n `{e.CAUSE_MESSAGE}`'
            await interaction.followup.send(embed=embed, ephemeral=True)
    @discord.ui.button(label="⏸️", style=discord.ButtonStyle.gray)
    async def pause_resume(self, interaction:discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or (self.player.is_connected and interaction.user.voice.channel.id != int(self.player.channel_id)):
            return await interaction.response.send_message(f'Подключитесь к каналу <#{self.player.channel_id}> чтобы использовать плеер.', ephemeral=True)
        if not self.paused:
            await self.player.set_pause(pause=True)
            self.paused = True
            for x in self.children:
                if isinstance(x, discord.ui.Button):
                    if x.label == '⏹️' or x.label == '📜' or x.label == '🔁':
                        continue
                    x.disabled = True
                elif isinstance(x, discord.ui.Select):
                    x.disabled = True
            button.style = discord.ButtonStyle.blurple
            button.disabled = False
            button.label = '▶️'
            await self.mess.edit(view=self)
        else:
            await self.player.set_pause(pause=False)
            self.paused = False
            for x in self.children:
                if isinstance(x, discord.ui.Button):
                    if x.label == '🔀' and len(self.player.queue) == 0:
                        continue
                    elif x.label == '⏭️' and len(self.player.queue) == 0:
                        continue
                    elif x.label == '⏮️':
                        continue
                    x.disabled = False
                elif isinstance(x, discord.ui.Select):
                    if len(self.ended) > 0:
                        x.disabled = False
            button.style = discord.ButtonStyle.gray
            button.label = '⏸️'
            await self.mess.edit(view=self)
        await interaction.response.defer()
    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.gray, disabled=True)
    async def next(self, interaction:discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or (self.player.is_connected and interaction.user.voice.channel.id != int(self.player.channel_id)):
            return await interaction.response.send_message(f'Подключитесь к каналу <#{self.player.channel_id}> чтобы использовать плеер.', ephemeral=True)
        await self.player.skip()
        if len(self.player.queue) == 0:
            button.disabled = True
            await self.mess.edit(view=self)
        await interaction.response.defer()
    @discord.ui.button(label="🔁", style=discord.ButtonStyle.gray)
    async def repeat(self, interaction:discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or (self.player.is_connected and interaction.user.voice.channel.id != int(self.player.channel_id)):
            return await interaction.response.send_message(f'Подключитесь к каналу <#{self.player.channel_id}> чтобы использовать плеер.', ephemeral=True)
        if not self.repeating:
            self.player.set_repeat(repeat=True)
            self.repeating = True
            button.style = discord.ButtonStyle.blurple
            for x in self.children:
                if isinstance(x, discord.ui.Button):
                    if x.label == '⏭️':
                        if not x.disabled:
                            x.disabled = True
                elif isinstance(x, discord.ui.Select):
                    if not x.disabled:
                        x.disabled = True
            await self.mess.edit(view=self)
        else:
            self.player.set_repeat(repeat=False)
            self.repeating = False
            x: discord.ui.Button
            for x in self.children:
                if isinstance(x, discord.ui.Button):
                    if x.label == '⏭️':
                        if x.disabled and len(self.player.queue) > 0:
                            x.disabled = False
                elif isinstance(x, discord.ui.Select):
                    done = False
                    if x.disabled:
                        for y in x.options:
                            if y.label == 'None':
                                done = True
                        if not done:
                            x.disabled = False
            button.style = discord.ButtonStyle.gray
            await self.mess.edit(view=self)
        await interaction.response.defer()
    @discord.ui.button(label="📜", style=discord.ButtonStyle.gray)
    async def queue_(self, interaction:discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or (self.player.is_connected and interaction.user.voice.channel.id != int(self.player.channel_id)):
            return await interaction.response.send_message(f'Подключитесь к каналу <#{self.player.channel_id}> чтобы использовать плеер.', ephemeral=True)
        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = 'Очередь:'
        description = ''
        count = 0
        for x in self.player.queue:
            count += 1
            description += f'`{count}.` [**{x.title}**]({x.uri})\n`Запросил:` **{self.bot.get_user(x.requester)}**\n'
        if description == '':
            description += 'В очереди нет треков.'
        embed.description = description
        await interaction.response.send_message(embed=embed, ephemeral=True)
    @discord.ui.button(label="🔊", style=discord.ButtonStyle.gray)
    async def volumeup(self, interaction:discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or (self.player.is_connected and interaction.user.voice.channel.id != int(self.player.channel_id)):
            return await interaction.response.send_message(f'Подключитесь к каналу <#{self.player.channel_id}> чтобы использовать плеер.', ephemeral=True)
        await self.player.set_volume(self.player.volume + 10)
        await interaction.response.defer()
    @discord.ui.button(label="🔀", style=discord.ButtonStyle.gray, disabled=True)
    async def shuffle(self, interaction:discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or (self.player.is_connected and interaction.user.voice.channel.id != int(self.player.channel_id)):
            return await interaction.response.send_message(f'Подключитесь к каналу <#{self.player.channel_id}> чтобы использовать плеер.', ephemeral=True)
        if not self.shuffled:
            self.player.set_shuffle(shuffle=True)
            self.shuffled = True
            button.style = discord.ButtonStyle.blurple
            await self.mess.edit(view=self)
        else:
            self.player.set_shuffle(shuffle=False)
            self.shuffled = False
            button.style = discord.ButtonStyle.gray
            await self.mess.edit(view=self)
        await interaction.response.defer()
    @discord.ui.button(label="🔉", style=discord.ButtonStyle.gray)
    async def volumedown(self, interaction:discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or (self.player.is_connected and interaction.user.voice.channel.id != int(self.player.channel_id)):
            return await interaction.response.send_message(f'Подключитесь к каналу <#{self.player.channel_id}> чтобы использовать плеер.', ephemeral=True)
        await self.player.set_volume(self.player.volume - 10)
        await interaction.response.defer()
    @discord.ui.button(label="⏩", style=discord.ButtonStyle.gray)
    async def seek(self, interaction:discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or (self.player.is_connected and interaction.user.voice.channel.id != int(self.player.channel_id)):
            return await interaction.response.send_message(f'Подключитесь к каналу <#{self.player.channel_id}> чтобы использовать плеер.', ephemeral=True)
        self.player.store(key='need_to_add', value=10)
        while True:
            seconds = self.player.fetch(key='seconds')
            if isinstance(seconds, int):
                self.player.delete(key='seconds')
                break
            await asyncio.sleep(0.3)
        await self.player.seek(position=(seconds + 10)*1000)
        await interaction.response.defer()
# SetInfo -------------------------------------------------------------------------------------------------------------------
class Bio(discord.ui.Modal, title='Расскажите всем кто вы такой!'):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)
    answer = discord.ui.TextInput(label='Ответ', style=discord.TextStyle.paragraph, placeholder='Писать сюда.', required=True, max_length=250)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            json.loads(str({"data": str(self.answer.value)}).replace("'", '"'))
        except json.JSONDecodeError:
            await interaction.response.send_message(f'Что то пошло не так... Попробуйте снова.', ephemeral=True)
            return
        res = await interaction.client.bd.fetch({'memberid': interaction.user.id, 'guildid': interaction.guild.id}, category='bio')
        if res.status:
            await interaction.client.bd.remove(res.value, category='bio')
        await interaction.client.bd.add({'memberid': interaction.user.id, 'guildid': interaction.guild.id, 'data': self.answer.value}, category='bio')
        await interaction.response.send_message(f'`Вы обновили свою биографию`:\n{self.answer.value}', ephemeral=True)
class Age(discord.ui.Modal, title='Сколько Вам лет?'):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)
    answer = discord.ui.TextInput(label='Ответ', style=discord.TextStyle.paragraph, placeholder='Писать сюда.', required=True, max_length=2)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            json.loads(str({"data": str(self.answer.value)}).replace("'", '"'))
        except json.JSONDecodeError:
            await interaction.response.send_message(f'Что то пошло не так... Попробуйте снова.', ephemeral=True)
            return
        res = await interaction.client.bd.fetch({'memberid': interaction.user.id, 'guildid': interaction.guild.id}, category='age')
        if res.status:
            await interaction.client.bd.remove(res.value, category='age')
        await interaction.client.bd.add({'memberid': interaction.user.id, 'guildid': interaction.guild.id, 'data': self.answer.value}, category='age')
        await interaction.response.send_message(f'`Вы обновили свой возраст!`:\n{self.answer.value}', ephemeral=True)
class Gender(discord.ui.Modal, title='Мальчик/Девочка?'):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)
    answer = discord.ui.TextInput(label='Ответ', style=discord.TextStyle.paragraph, placeholder='Писать сюда.', required=True, max_length=25)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            json.loads(str({"data": str(self.answer.value)}).replace("'", '"'))
        except json.JSONDecodeError:
            await interaction.response.send_message(f'Что то пошло не так... Попробуйте снова.', ephemeral=True)
            return
        res = await interaction.client.bd.fetch({'memberid': interaction.user.id, 'guildid': interaction.guild.id}, category='gender')
        if res.status:
            await interaction.client.bd.remove(res.value, category='gender')
        await interaction.client.bd.add({'memberid': interaction.user.id, 'guildid': interaction.guild.id, 'data': self.answer.value}, category='gender')
        await interaction.response.send_message(f'`Вы обновили свой Пол!`:\n{self.answer.value}', ephemeral=True)
class Name(discord.ui.Modal, title='Как вас зовут?'):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)
    answer = discord.ui.TextInput(label='Ответ', style=discord.TextStyle.paragraph, placeholder='Писать сюда.', required=True, max_length=50)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            json.loads(str({"data": self.answer.value}).replace("'", '"'))
        except json.JSONDecodeError:
            return await interaction.response.send_message(f'Что то пошло не так... Попробуйте снова.', ephemeral=True)
        res = await interaction.client.bd.fetch({'memberid': interaction.user.id, 'guildid': interaction.guild.id}, category='name')
        if res.status:
            await interaction.client.bd.remove(res.value, category='name')
        await interaction.client.bd.add({'memberid': interaction.user.id, 'guildid': interaction.guild.id, 'data': self.answer.value}, category='name')
        await interaction.response.send_message(f'`Вы обновили своё Имя!`:\n{self.answer.value}', ephemeral=True)
class SetInfo(discord.ui.View):
    def __init__(self, *, timeout=180.0, ctx: commands.Context):
        super().__init__(timeout=timeout)
        self.add_item(closeButton(label='❌Выход', style=discord.ButtonStyle.red))
        self.ctx=ctx
    @discord.ui.select(placeholder='Выберите опцию...', options=[
        discord.SelectOption(label="Заполнить биографию."),
        discord.SelectOption(label="Указать возраст."),
        discord.SelectOption(label="Указать пол."),
        discord.SelectOption(label="Указать имя.")
        ])
    async def infoset(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == 'Заполнить биографию.':
            await interaction.response.send_modal(Bio())
        elif select.values[0] == 'Указать возраст.':
            await interaction.response.send_modal(Age())
        elif select.values[0] == 'Указать пол.':
            await interaction.response.send_modal(Gender())
        elif select.values[0] == 'Указать имя.':
            await interaction.response.send_modal(Name())
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(embed=discord.Embed(title='Error', description='Вы не можете взаимодействовать с этим сообщением, т.к его вызвал другой человек.', color=discord.Color.red()), ephemeral=True)
            return False
        return True
    async def on_timeout(self):
        self.stop()
# Tickets ----------------------------------------------------------------------------------------------------------
class TicketClose(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.aboba_value = []
    @discord.ui.button(label="Закрыть Канал.", style=discord.ButtonStyle.red, custom_id='CloseBTNTickets')
    async def close(self, interaction:discord.Interaction, button: discord.ui.Button):
        if not interaction.user.id in self.aboba_value:
            self.aboba_value.append(interaction.user.id)
            return await interaction.response.send_message(content='`Вы точно хотите закрыть этот тикет?`', ephemeral=True)
        button.disabled = True
        await interaction.message.edit(view=self)
        self.aboba_value.remove(interaction.user.id)
        res = await interaction.client.bd.fetch({'channelid': interaction.channel.id}, category='ticketusers')
        if res.status:
            member = await interaction.client.fetch_user(int(res.value['memberid']))
            await interaction.channel.set_permissions(target=member, overwrite=discord.PermissionOverwrite(send_messages=False, read_messages=True))
        await interaction.response.send_message(content='`Канал удалится через 10 секунд...`')
        await asyncio.sleep(10)
        try:
            await interaction.client.bd.remove({'channelid': interaction.channel.id}, category='ticketusers')
            await interaction.channel.delete()
        except discord.errors.NotFound:
            return
class TicketButtons(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
    @discord.ui.button(label="Создать Тикет",emoji='📨', style=discord.ButtonStyle.green, custom_id='CreateTicket')
    async def ticket(self, interaction:discord.Interaction, button: discord.ui.Button):
        res = await interaction.client.bd.fetch({'guildid': interaction.guild.id}, category='tickets')
        value = res.value
        category = discord.utils.get(interaction.guild.categories, id=value['catid'])
        await interaction.response.defer(ephemeral=True, thinking=True)
        res = await interaction.client.bd.fetch({'memberid': interaction.user.id, 'guildid': interaction.guild.id}, category='ticketusers')
        if res.status:
            channel = interaction.client.get_channel(int(res.value["channelid"]))
            if channel is not None:
                await interaction.followup.send(content=f'Перейдите в канал <#{res.value["channelid"]}>.', ephemeral=True)
                return
            else:
                await interaction.client.bd.remove({'channelid': res.value["channelid"]}, category='ticketusers')
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True)
            }          
        try:
            all = await interaction.client.bd.fetch({}, mode='all', category='ticketsperms')
            for i in all.value:
                if interaction.guild.id == int(i['guildid']):
                    for j in i['roles']:
                        role = interaction.guild.get_role(int(j))
                        overwrites[role] =  discord.PermissionOverwrite(view_channel=True, send_messages=True)
        except Exception:
            pass
        channel = await interaction.guild.create_text_channel(f"Тикет {interaction.user.name}", category=category, overwrites=overwrites)
        await interaction.client.bd.add({'memberid': interaction.user.id, 'guildid': interaction.guild.id, 'channelid': channel.id}, category='ticketusers')
        await interaction.followup.send(content=f'Канал <#{channel.id}> создан.', ephemeral=True)
        embed = ViolaEmbed()
        embed.description = '**Ваш тикет был успешно создан! Не стесняйтесь задавать любые вопросы!**'
        await channel.send(content=f'<@!{interaction.user.id}>', embed=embed, view=TicketClose())
# Rooms -----------------------------------------------------------------------------------------------------------
class RoomsCallback(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
    @discord.ui.select(placeholder='Выберите опцию...', options=[
        discord.SelectOption(label="Добавить приватные комнаты."),
        discord.SelectOption(label="Удалить приватные комнаты."),
        discord.SelectOption(label="Настроить комнаты."),
        ])
    async def roomsactions(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == 'Добавить приватные комнаты.':
            await interaction.response.defer(ephemeral= True, thinking= True)
            res = await interaction.client.bd.fetch({'guildid': interaction.guild.id}, category='rooms')
            if not res.status:
                category = await interaction.guild.create_category(name='- Приватные комнаты -', reason='private rooms')
                channel = await category.create_voice_channel(name='Создать канал [+]', reason='private rooms', user_limit=1)
                channel2 = await category.create_text_channel(name='Управление📡', reason='private rooms')
                # --------------------------------------------
                embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message))
                embed.title = 'Приватные комнаты.'
                description = f'`👪 Изменить лимит канала`\t`🚮 Забрать/Выдать доступ`\n`💁‍♂️ Добавить владельца`\t`🚪 Скрыть/Открыть комнату`\n`📝 Изменить название`\t`🎙️ заглушить/разглушить кого-то`'
                embed.description = description
                await channel2.send(embed=embed, view=RoomActions())
                # --------------------------------------------
                await interaction.client.bd.add({'guildid': interaction.guild.id, 'voiceid': channel.id, 'catid': category.id, 'textid': channel2.id}, category='rooms')
                embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message))
                embed.description = '`Приватные голосовые комнаты успешно созданы.`'
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
                embed.description = f'`Эта функция уже включена на этом сервере.`\n`Канал:` <#{res.value["voiceid"]}>\n**(Если Категория или один из каналов были удалены, вы можете пересоздать систему приватных комнат.)**'
                await interaction.followup.send(embed=embed, ephemeral=True)
        elif select.values[0] == 'Удалить приватные комнаты.':
            await interaction.response.defer(ephemeral= True, thinking= True)
            res = await interaction.client.bd.fetch({'guildid': interaction.guild.id}, category='rooms')
            if not res.status:
                embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
                embed.description = '`Чтобы удалить систему приватных комнат, ее нужно для начала создать.`'
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=int(res.value['catid']))
                try:
                    for x in category.channels:
                        await x.delete()
                    await category.delete()
                except Exception:
                    pass
                await interaction.client.bd.remove({'guildid': interaction.guild.id}, category='rooms')
                embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message))
                embed.description = '`Система приватных комнат успешно удалена.`'
                await interaction.followup.send(embed=embed, ephemeral=True)
class RoomActions(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.used = []
    @discord.ui.button(label="👪", style=discord.ButtonStyle.gray, custom_id='1') # Limit
    async def limit(self, interaction:discord.Interaction, button: discord.ui.Button):
        res = await interaction.client.bd.fetch({'guildid': interaction.guild.id}, category='rooms')
        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=int(res.value['catid']))
        if not interaction.user.voice:
            embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
            embed.description = '`Вам необходимо зайти в голосовой канал, чтобы использовать это.`'
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if interaction.user.voice.channel not in category.voice_channels:
            embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
            embed.description = '`Этот канал не относится к приватным комнатам.`'
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if interaction.user.id in self.used:
            return await interaction.response.send_message('`Завершите предыдущее действие прежде чем начинать новое.`', ephemeral=True)
        if interaction.user.voice.channel.overwrites_for(interaction.user).manage_channels:
            self.used.append(interaction.user.id)
            await interaction.response.send_message('`Укажите лимит канала от 1 до 99:`', ephemeral=True)
            try:
                msg: discord.Message = await interaction.client.wait_for('message', timeout=60.0, check=lambda m: m.author.id==interaction.user.id)
                await msg.delete()
            except asyncio.TimeoutError:
                self.used.remove(interaction.user.id)
                return
            try:
                amount = int(msg.content)
            except ValueError:
                self.used.remove(interaction.user.id)
                return await interaction.followup.send(f'`Неверный формат. Укажите число от 1 до 99 включительно.`', ephemeral=True)
            if amount < 1 or amount > 99:
                self.used.remove(interaction.user.id)
                return await interaction.followup.send(f'`Укажите число от 1 до 99 включительно.`', ephemeral=True)
            await interaction.user.voice.channel.edit(user_limit=amount)
            await interaction.followup.send(f'`Лимит канала изменен на {amount}`', ephemeral=True)
            self.used.remove(interaction.user.id)
        else:
            return await interaction.response.send_message('`У вас не хватает прав сделать это действие!`', ephemeral=True)
    @discord.ui.button(label="🚮", style=discord.ButtonStyle.gray, custom_id='2')
    async def ban(self, interaction:discord.Interaction, button: discord.ui.Button):
        res = await interaction.client.bd.fetch({'guildid': interaction.guild.id}, category='rooms')
        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=int(res.value['catid']))
        if not interaction.user.voice:
            embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
            embed.description = '`Вам необходимо зайти в голосовой канал, чтобы использовать это.`'
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if interaction.user.voice.channel not in category.voice_channels:
            embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
            embed.description = '`Этот канал не относится к приватным комнатам.`'
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if interaction.user.id in self.used:
            return await interaction.response.send_message('`Завершите предыдущее действие прежде чем начинать новое.`', ephemeral=True)
        if interaction.user.voice.channel.overwrites_for(interaction.user).manage_channels:
            self.used.append(interaction.user.id)
            await interaction.response.send_message('`Укажите пользователя, которому хотите ограничить доступ к комнате или выдать его обратно упомянув его или отправив в чат его id:`', ephemeral=True)
            try:
                msg: discord.Message = await interaction.client.wait_for('message', timeout=60.0, check=lambda m: m.author.id==interaction.user.id)
                await msg.delete()
            except asyncio.TimeoutError:
                self.used.remove(interaction.user.id)
                return
            member = interaction.guild.get_member(int(msg.content.replace("<@", '').replace(">", '')))
            if member.id == interaction.user.id:
                self.used.remove(interaction.user.id)
                await interaction.followup.send(f'`Вы не можете забанить самого себя.`', ephemeral=True)
                return
            if member is None:
                self.used.remove(interaction.user.id)
                await interaction.followup.send(f'`Не удалось найти этого пользователя.`', ephemeral=True)
                return
            if interaction.user.voice.channel.permissions_for(interaction.user).view_channel:
                await interaction.user.voice.channel.set_permissions(member, connect=False)
                await member.move_to(None)
                self.used.remove(interaction.user.id)
                await interaction.followup.send(f'`Вы успешно забанили {member} в вашем голосовом канале`', ephemeral=True)
            else:
                await interaction.user.voice.channel.set_permissions(member, connect=True)
                self.used.remove(interaction.user.id)
                await interaction.followup.send(f'`Вы успешно выдали {member} доступ к вашему голосовому каналу.`', ephemeral=True)
        else:
            await interaction.response.send_message('`У вас не хватает прав сделать это действие!`', ephemeral=True)
    @discord.ui.button(label="💁‍♂️", style=discord.ButtonStyle.gray, custom_id='3')
    async def transfer(self, interaction:discord.Interaction, button: discord.ui.Button):
        res = await interaction.client.bd.fetch({'guildid': interaction.guild.id}, category='rooms')
        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=int(res.value['catid']))
        if not interaction.user.voice:
            embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
            embed.description = '`Вам необходимо зайти в голосовой канал, чтобы использовать это.`'
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if interaction.user.voice.channel not in category.voice_channels:
            embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
            embed.description = '`Этот канал не относится к приватным комнатам.`'
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if interaction.user.id in self.used:
            return await interaction.response.send_message('`Завершите предыдущее действие прежде чем начинать новое.`', ephemeral=True)
        if interaction.user.voice.channel.overwrites_for(interaction.user).manage_channels:
            self.used.append(interaction.user.id)
            await interaction.response.send_message('`Укажите пользователя, которому хотите отдать доступ к комнате упомянув его или отправив в чат его id:`', ephemeral=True)
            try:
                msg: discord.Message = await interaction.client.wait_for('message', timeout=60.0, check=lambda m: m.author.id==interaction.user.id)
                await msg.delete()
            except asyncio.TimeoutError:
                self.used.remove(interaction.user.id)
                return
            member = interaction.guild.get_member(int(msg.content.replace("<@", '').replace(">", '')))
            if member.id == interaction.user.id:
                self.used.remove(interaction.user.id)
                return await interaction.followup.send(f'`Вы не можете добавить самого себя как владельца.`', ephemeral=True)
            if member is None:
                self.used.remove(interaction.user.id)
                return await interaction.followup.send(f'`Не удалось найти этого пользователя.`', ephemeral=True)
            overwrites = {
                # interaction.user: discord.PermissionOverwrite(manage_channels=False),
                member: discord.PermissionOverwrite(manage_channels=True)
            }
            await interaction.user.voice.channel.edit(overwrites=overwrites)
            self.used.remove(interaction.user.id)
            await interaction.followup.send(f'`Вы успешно сделали владельцем комнаты {member}.`', ephemeral=True)
        else:
            await interaction.response.send_message('`У вас не хватает прав сделать это действие!`', ephemeral=True)
    @discord.ui.button(label="🚪", style=discord.ButtonStyle.gray, custom_id='4')
    async def show(self, interaction:discord.Interaction, button: discord.ui.Button):
        res = await interaction.client.bd.fetch({'guildid': interaction.guild.id}, category='rooms')
        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=int(res.value['catid']))
        if not interaction.user.voice:
            embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
            embed.description = '`Вам необходимо зайти в голосовой канал, чтобы использовать это.`'
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if interaction.user.voice.channel not in category.voice_channels:
            embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
            embed.description = '`Этот канал не относится к приватным комнатам.`'
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if interaction.user.voice.channel.overwrites_for(interaction.user).manage_channels:
            if interaction.user.voice.channel.overwrites_for(interaction.guild.default_role).view_channel:
                await interaction.user.voice.channel.set_permissions(interaction.guild.default_role, view_channel=False)
                await interaction.response.send_message("`Вы успешно скрыли канал от чужих глаз. 👀`", ephemeral=True)
            else:
                await interaction.user.voice.channel.set_permissions(interaction.guild.default_role, view_channel=True)
                await interaction.response.send_message("`Теперь кто угодно может подключаться к вашему голосовому каналу.`", ephemeral=True)
        else:
            await interaction.response.send_message('`У вас не хватает прав сделать это действие!`', ephemeral=True)
    @discord.ui.button(label="📝", style=discord.ButtonStyle.gray, custom_id='5')
    async def rename(self, interaction:discord.Interaction, button: discord.ui.Button):
        res = await interaction.client.bd.fetch({'guildid': interaction.guild.id}, category='rooms')
        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=int(res.value['catid']))
        if not interaction.user.voice:
            embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
            embed.description = '`Вам необходимо зайти в голосовой канал, чтобы использовать это.`'
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if interaction.user.voice.channel not in category.voice_channels:
            embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
            embed.description = '`Этот канал не относится к приватным комнатам.`'
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if interaction.user.id in self.used:
            return await interaction.response.send_message('`Завершите предыдущее действие прежде чем начинать новое.`', ephemeral=True)
        if interaction.user.voice.channel.overwrites_for(interaction.user).manage_channels:
            self.used.append(interaction.user.id)
            await interaction.response.send_message('`Укажите новое название для комнаты:`', ephemeral=True)
            try:
                msg: discord.Message = await interaction.client.wait_for('message', timeout=60.0, check=lambda m: m.author.id==interaction.user.id)
                await msg.delete()
            except asyncio.TimeoutError:
                self.used.remove(interaction.user.id)
                return
            if len(msg.content) > 99:
                self.used.remove(interaction.user.id)
                await interaction.response.send_message('`Укажите название длиной до 100 символов.`', ephemeral=True)
                return
            await interaction.user.voice.channel.edit(name=msg.content)
            self.used.remove(interaction.user.id)
            await interaction.followup.send(f'`Вы успешно переименовали комнату.`', ephemeral=True)
        else:
            await interaction.response.send_message('`У вас не хватает прав сделать это действие!`', ephemeral=True)
    @discord.ui.button(label=">", style=discord.ButtonStyle.gray, disabled=True, custom_id='6')
    async def dummy1(self, interaction:discord.Interaction, button: discord.ui.Button):
        pass
    @discord.ui.button(label=">", style=discord.ButtonStyle.gray, disabled=True, custom_id='7')
    async def dummy2(self, interaction:discord.Interaction, button: discord.ui.Button):
        pass
    @discord.ui.button(label="🎙️", style=discord.ButtonStyle.gray, custom_id='8')
    async def muteunmute(self, interaction:discord.Interaction, button: discord.ui.Button):
        res = await interaction.client.bd.fetch({'guildid': interaction.guild.id}, category='rooms')
        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=int(res.value['catid']))
        if not interaction.user.voice:
            embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
            embed.description = '`Вам необходимо зайти в голосовой канал, чтобы использовать это.`'
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if interaction.user.voice.channel not in category.voice_channels:
            embed = ViolaEmbed(ctx=await interaction.client.get_context(interaction.message), format='error')
            embed.description = '`Этот канал не относится к приватным комнатам.`'
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if interaction.user.id in self.used:
            return await interaction.response.send_message('`Завершите предыдущее действие прежде чем начинать новое.`', ephemeral=True)
        if interaction.user.voice.channel.overwrites_for(interaction.user).manage_channels:
            self.used.append(interaction.user.id)
            await interaction.response.send_message('`Укажите пользователя, которого хотите лишить права голоса или наоборот упомянув его или указав его id:`', ephemeral=True)
            try:
                msg: discord.Message = await interaction.client.wait_for('message', timeout=60.0, check=lambda m: m.author.id==interaction.user.id)
                await msg.delete()
            except asyncio.TimeoutError:
                self.used.remove(interaction.user.id)
                return
            member = interaction.guild.get_member(int(msg.content.replace("<@", '').replace(">", '')))
            if member.id == interaction.user.id:
                await interaction.followup.send(f'`Вы не можете взаимодействовать с самим собой.`', ephemeral=True)
                self.used.remove(interaction.user.id)
                return
            if member is None:
                self.used.remove(interaction.user.id)
                await interaction.followup.send(f'`Не удалось найти этого пользователя.`', ephemeral=True)
                return
            if member.voice.mute:
                await member.edit(mute=False)
                self.used.remove(interaction.user.id)
                await interaction.followup.send(f'`Вы успешно размутили {member}!`', ephemeral=True)
            else:
                await member.edit(mute=True)
                self.used.remove(interaction.user.id)
                await interaction.followup.send(f'`Вы успешно лишили права голоса {member}`', ephemeral=True)
    @discord.ui.button(label="<", style=discord.ButtonStyle.gray, disabled=True, custom_id='9')
    async def dummy3(self, interaction:discord.Interaction, button: discord.ui.Button):
        pass
    @discord.ui.button(label="<", style=discord.ButtonStyle.gray, disabled=True, custom_id='10')
    async def dummy4(self, interaction:discord.Interaction, button: discord.ui.Button):
        pass
# Other --------------------------------------------------------------------------------------------
class LavalinkVoiceClient(discord.VoiceClient):
    def __init__(self, client: commands.Bot, channel: discord.abc.Connectable) -> None:
        self.client = client
        self.channel = channel
        self.lavalink: lavalink.Client = self.client.lavalink
    async def on_voice_server_update(self, data) -> None:
        lavalink_data = {'t': 'VOICE_SERVER_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)
    async def on_voice_state_update(self, data) -> None:
        lavalink_data = {'t': 'VOICE_STATE_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)
    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False) -> None:
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)
    async def disconnect(self, *, force: bool = False) -> None:
        player: lavalink.DefaultPlayer = self.lavalink.player_manager.get(self.channel.guild.id)
        if not force and not player.is_connected:
            return
        await self.channel.guild.change_voice_state(channel=None)
        player.channel_id = None
        self.cleanup()
class ViolaEmbed(discord.Embed):
    def __init__(self, **kwargs) -> None:
        self.format = kwargs.pop('format', 'success')
        self.ctx = kwargs.pop('ctx', None)
        if not isinstance(self.ctx, commands.Context) and self.ctx is not None:
            raise discord.errors.ClientException('ctx is not commands.Context object')
        super().__init__(**kwargs)
        if self.ctx:
            try:
                self.set_footer(text=f'{self.ctx.guild.name}', icon_url=f'{self.ctx.guild.icon.url}')
            except Exception:
                self.set_footer(text=f'{self.ctx.guild.name}', icon_url=f'{self.ctx.bot.user.avatar.url}')
            try:
                self.set_thumbnail(url=f'{self.ctx.guild.icon.url}')
            except Exception:
                self.set_thumbnail(url=self.ctx.bot.user.avatar.url)
        colors = {'success': discord.Color.green(), 'warning': discord.Color.yellow(), 'error': discord.Color.red()}
        titles = {'success': 'Успешно.', 'warning': 'Внимание.', 'error': 'Ошибка.'}
        urls = {
            'success': 'https://cdn.discordapp.com/emojis/1006317088253681734.webp',
            'warning': 'https://cdn.discordapp.com/emojis/1006317089683951718.webp',
            'error': 'https://cdn.discordapp.com/emojis/1006317086471094302.webp'
        }
        self.set_author(icon_url=urls[self.format], name=titles[self.format])
        self.color = colors[self.format]