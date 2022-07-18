import discord, requests, json, datetime, os, asyncio, random, traceback, time, sys, emoji
from discord.ext import commands
from discord.utils import get
from discord.ext.commands import has_permissions
from Config.assets.database import DataBase
_ids = []
ids_ = []
botik = None
# -----------------------------------------------------------------------------------------------------------
class cmds(commands.Cog):
    def __init__(self, bot: commands.Bot):
        global botik
        self.bot = bot
        botik = self.bot

    @commands.command()
    @has_permissions(administrator=True)
    async def delete(self, ctx: commands.Context):
        if not ctx.channel.id in _ids:
            _ids.append(ctx.channel.id)
        else:
            try:
                await ctx.message.delete()
            except discord.errors.NotFound:
                return
            return
        await ctx.message.delete()
        def check(reaction, user):
            return user == ctx.message.author and reaction.emoji == '❤️'
        try:
            mess = await ctx.send('`Вы уверены что хотите удалить канал?`')
            await mess.add_reaction('❤️')
            await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
            await mess.delete()
            await ctx.send('`Канал удалится через 10 секунд...`')
            await asyncio.sleep(10)
            try:
                await ctx.channel.delete()
                _ids.remove(ctx.channel.id)
            except discord.errors.NotFound:
                return
        except asyncio.TimeoutError:
            try:
                await mess.delete()
                _ids.remove(ctx.channel.id)
            except discord.errors.NotFound:
                return
            return

    @commands.command(aliases = ['reaction-roles', ])
    @has_permissions(administrator=True)
    async def reactions(self, ctx: commands.Context, *params):
        if ctx.channel.id in ids_:
            return
        try:
            if not params:
                args = []
                # -------------------------------------------------------------------------------
                def check(reaction, user):
                    return user == ctx.message.author and reaction.emoji == '✅'
                try:
                    mess = await ctx.send('`Роли за реакцию. Начнем?`')
                    await mess.add_reaction('✅')
                    await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
                    ids_.append(ctx.channel.id)
                    args.append('add')
                except asyncio.TimeoutError:
                    try:
                        await mess.delete()
                    except discord.errors.NotFound:
                        ids_.remove(ctx.channel.id)
                        return
                    ids_.remove(ctx.channel.id)
                    return
                # -------------------------------------------------------------------------------
                def check(m: discord.Message):
                    return m.author == ctx.message.author and m.channel == ctx.channel
                try:
                    mess = await ctx.send('`Введите id канала:`')
                    msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                    channel = self.bot.get_channel(int(msg.content))
                    if channel is not None and channel.guild.id == ctx.guild.id:
                        args.append(channel.id)
                    else:
                        await ctx.send('`Канал не найден. Процесс прерван.`')
                        ids_.remove(ctx.channel.id)
                        return
                except asyncio.TimeoutError:
                    try:
                        await mess.delete()
                        ids_.remove(ctx.channel.id)
                        return
                    except discord.errors.NotFound:
                        ids_.remove(ctx.channel.id)
                        return
                # -------------------------------------------------------------------------------
                def check(m: discord.Message):
                    return m.author == ctx.message.author and m.channel == ctx.channel
                try:
                    mess = await ctx.send('`Введите id Сообщения:`')
                    msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                    message = await channel.fetch_message(int(msg.content))
                    if message is not None and message.channel.guild.id == ctx.guild.id:
                        args.append(message.id)
                    else:
                        await ctx.send('`Сообщение не найдено. Процесс прерван.`')
                        ids_.remove(ctx.channel.id)
                        return
                except asyncio.TimeoutError:
                    try:
                        await mess.delete()
                        ids_.remove(ctx.channel.id)
                        return
                    except discord.errors.NotFound:
                        ids_.remove(ctx.channel.id)
                        return
                # -------------------------------------------------------------------------------
                def check(m: discord.Message):
                    return m.author == ctx.message.author and m.channel == ctx.channel
                try:
                    mess = await ctx.send(f'`Отправьте нужную вам реакцию в чат:`')
                    msg1 = await self.bot.wait_for('message', timeout=30.0, check=check)
                    args.append(msg1.content)
                except asyncio.TimeoutError:
                    try:
                        await mess.delete()
                        ids_.remove(ctx.channel.id)
                        return
                    except discord.errors.NotFound:
                        ids_.remove(ctx.channel.id)
                        return
                # -------------------------------------------------------------------------------
                def check(m: discord.Message):
                    return m.author == ctx.message.author and m.channel == ctx.channel
                try:
                    mess = await ctx.send(f'`Укажите роль упоминанием или ее id:`')
                    msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                    role = get(ctx.guild.roles, id=int(msg.content.replace('<@&', '').replace('>', '')))
                    if role is not None:
                        args.append(role.id)
                    else:
                        await ctx.send('`Роль не найдена. Процесс прерван.`')
                        ids_.remove(ctx.channel.id)
                        return
                except asyncio.TimeoutError:
                    try:
                        await mess.delete()
                        ids_.remove(ctx.channel.id)
                        return
                    except discord.errors.NotFound:
                        ids_.remove(ctx.channel.id)
                        return
                # -------------------------------------------------------------------------------
                if args[0] == 'add':
                    channel = self.bot.get_channel(int(str(args[1]).replace('<#', '').replace('>', '')))
                    try:
                        message = await channel.fetch_message(int(args[2]))
                    except discord.errors.NotFound:
                        message = None
                    done = False
                    if emoji.emoji_count([args[3]]) == 0:
                        reaction = None
                        for i in self.bot.emojis:
                            if str(i) == str(args[3]):
                                reaction = i
                                done = True
                                break
                    else:
                        reaction = args[3]
                    if reaction is None:
                        await msg1.reply('`Бот не знает такой реакции.`')
                        ids_.remove(ctx.channel.id)
                        return
                    role = get(ctx.guild.roles, id=int(str(args[4]).replace('<@&', '').replace('>', '')))
                    if message is not None and channel is not None and role is not None:
                        txt = DataBase('reactroles')
                        if done:
                            res = txt.add({'channel_id': channel.id, 'message_id': message.id, 'reaction': reaction.name, 'role_id': role.id})
                            await message.add_reaction(reaction)
                        else:
                            res = txt.add({'channel_id': channel.id, 'message_id': message.id, 'reaction': reaction, 'role_id': role.id})
                            await message.add_reaction(reaction)
                        if str(res['cleared']) == '1':
                            await ctx.send('`Такой параметр уже существует.`')
                            ids_.remove(ctx.channel.id)
                            return
                        if done:
                            if not reaction.animated:
                                react = f'<:{reaction.name}:{reaction.id}>'
                            else:
                                react = f'<a:{reaction.name}:{reaction.id}>'
                        else:
                            react = f'{reaction}'
                        await ctx.send(embed=discord.Embed(title='Роли за реакцию.', description=f'Параметр добавлен.\nКанал: <#{channel.id}>\nid сообщения: [**{message.id}**]({message.jump_url})\nРеакция: {react}\nРоль: <@&{role.id}>', color=discord.Color.green()))
            else:
                if params[0] == 'help':
                    await ctx.send('`s!reaction-roles <remove/view> <message_id>`')
                elif params[0] == 'remove':
                    txt = DataBase('reactroles')
                    try:
                        channel = self.bot.get_channel(int(json.loads(txt.fetch('message_id', int(params[1]))['value'].replace("'", '"').replace('\n', ''))['channel_id']))
                    except KeyError:
                        await ctx.send('`Сообщение не найдено в базе.`')
                        ids_.remove(ctx.channel.id)
                        return
                    res = txt.fetch('message_id', int(params[1]))
                    if res['success'] == 'True':
                        def check(reaction, user):
                            return user == ctx.message.author and reaction.emoji == '💔'
                        try:
                            mess = await ctx.send('`Удалить все параметры связанные с этим сообщением?`')
                            await mess.add_reaction('💔')
                            await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
                            await mess.clear_reactions()
                            txt.remove('message_id', int(params[1]))
                            await mess.edit('`Все параметры связанные с этим сообщением очищены.`')
                        except asyncio.TimeoutError:
                            try:
                                await mess.delete()
                            except discord.errors.NotFound:
                                ids_.remove(ctx.channel.id)
                                return
                            ids_.remove(ctx.channel.id)
                            return
                elif params[0] == 'view':
                    txt = DataBase('reactroles')
                    try:
                        channel = self.bot.get_channel(int(json.loads(txt.fetch('message_id', int(params[1]))['value'].replace("'", '"').replace('\n', ''))['channel_id']))
                    except KeyError:
                        await ctx.send('`Сообщение не найдено в базе.`')
                        return
                    message = await channel.fetch_message(int(params[1]))
                    res = txt.fetchl('message_id', int(params[1]))
                    info = ''
                    if res['success'] == 'True':
                        for i in res['value']:
                            i = json.loads(str(i).replace("'", '"').replace('\n', ''))
                            info += f'Реакция: {i["reaction"]} ---> Роль: <@&{i["role_id"]}>\n'
                        embed = discord.Embed(title="Роли за реакцию.", description=f"id сообщения: [{message.id}]({message.jump_url})\n{info}")
                        embed.color = 0x00ffff
                        await ctx.send(embed=embed)
        except Exception as e:
            print(traceback.format_exc())
            ids_.remove(ctx.channel.id)
            await ctx.send(f'`Что то пошло не так... {e}`')

    @commands.command()
    async def ping(self, ctx: commands.Context):
        ping1 = f"{str(round(self.bot.latency * 1000))} ms"
        embed = discord.Embed(title = "**Pong!**", description = "`" + ping1 + "`", color = 0xafdafc)
        await ctx.send(embed = embed)

    @commands.command()
    @has_permissions(administrator=True)
    async def setprefix(self, ctx: commands.Context, prefix):
        def getprefix():
            txt = DataBase('prefixes')
            res = txt.fetch('guildid', ctx.guild.id)
            if res['success'] == 'True':
                msg = res['value'].replace("'", '"').replace('\n', '')
                msg = json.loads(msg)
                return msg['prefix'] == prefix
            else:
                return 's!' == prefix
        async def e1(ctx: commands.Context, mess: discord.Message):
            await mess.edit(embed=discord.Embed(title='Смена префикса.', description=f'Префикс сервера {ctx.guild.name} теперь: `{prefix}`', color=0x00ffff))
        async def c2(ctx: commands.Context, mess: discord.Message):
            await mess.clear_reactions()
        if getprefix():
            await ctx.send(embed=discord.Embed(title='Ошибка.', description=f'Префикс сервера {ctx.guild.name} уже `{prefix}`. Нет смысла его менять.', color=0x00ffff))
            return
        def check(reaction, user):
            return user == ctx.message.author and reaction.emoji == '✅'
        try:
            mess = await ctx.send(embed=discord.Embed(title='Смена префикса.', description=f'Сменить префикс сервера {ctx.guild.name} на `{prefix}`?', color=0x00ffff))
            await mess.add_reaction('✅')
            await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
            self.bot.loop.create_task(c2(ctx, mess))
            self.bot.loop.create_task(e1(ctx, mess))
            txt = DataBase('prefixes')
            txt.add({'guildid': ctx.guild.id, 'prefix': f'{prefix}'}, 'guildid')
        except asyncio.TimeoutError:
            try:
                await mess.delete()
            except discord.errors.NotFound:
                return

    @commands.command(aliases = ['vc-members', ])
    @has_permissions(administrator=True)
    async def member_count(self, ctx: commands.Context, *args):
        if args[0] == 'remove':
            id = int(str(args[1]).replace('<#', '').replace('>', ''))
            channel = self.bot.get_channel(id)
            if not channel.guild.id == ctx.guild.id:
                await ctx.send(f'`Канал не найден`')
                return
            txt = DataBase('voicemembers')
            a = txt.remove('voiceid', id)
            guild = self.bot.get_guild(int(channel.guild.id))
            if a['done'] == 'True':
                await ctx.send(f'`{channel.name} удален из {guild.name}`')
            else:
                await ctx.send(f'`Канал не найден`')
            return
        id = int(str(args[0]).replace('<#', '').replace('>', ''))
        channel = self.bot.get_channel(id)
        txt = DataBase('voicemembers')
        if channel:
            info = txt.add({'guildid': channel.guild.id, 'voiceid': id, 'name': str(channel.guild.name).replace(',', '').replace("'",'')}, 'guildid')
            if info['added'] == 'True':
                await ctx.send(f'`Канал успешно добавлен. Канал: {channel.name}`')
                guild = self.bot.get_guild(int(channel.guild.id))
                await channel.edit(name=f"Участников: {guild.member_count}")
                return
            elif info['replaced'] == 'True':
                await ctx.send(f'`Канал успешно обновлен. Новый канал: {channel.name}`')
                guild = self.bot.get_guild(int(channel.guild.id))
                await channel.edit(name=f"Участников: {guild.member_count}")
                return
        else:
            await ctx.send(f'`Канал не найден.`')

    @commands.command()
    async def help(self, ctx: commands.Context):
        # com1 = "`s!link <ign>`/`s!unlink`: Link/Unlink your account.\n`s!gtop <*day> <name>`: Display guild top by exp.\n`s!s <*ign>`: Showing your hypixel stats.\n`s!reply <content>`: Replying to message.\n`s!vcm <channel_id | mention>`: Mutes everyone in voice channel\n"
        # com2 = "`s!say <content>` sends content in chat\n`s!ship <user mention | name> <user mention | name>`: fun command.\n`s!vc-members <channel_id | mention> OR remove <channel_id | mention>`"
        # com3 = "`s!tickets <create/remove>`: Система жалоб и тикетов."
        com1 = '**Hypixel**:\n`s!link, s!unlink`\n`s!gtop, s!s`\n\n'
        com2 = '**Команды**:\n`s!reply, s!vcm`\n`s!say, s!ship`\n`s!vc-members <remove>, s!tickets <create/remove/perms>`\n `s!reaction-roles <view/remove>`\n`s!setprefix, s!ping`'
        embed = discord.Embed(title="Help", description=com1+com2, color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command()
    async def ship(self, ctx: commands.Context, *args):
        if not args or len(args) != 2:
            await ctx.send('`s!ship <name1> <name2>`')
            return
        name = args[0]
        name2 = args[1]
        if len(name) == 21:
            name = str(name).replace('<@', '').replace('>', '')
            name = self.bot.get_user(int(name)).name
        if len(name2) == 21:
            name2 = str(name2).replace('<@', '').replace('>', '')
            name2 = self.bot.get_user(int(name2)).name
        shipname = name[:len(name)//2] + str(name2).replace(str(name2[:len(args[1])//2]), '')
        compatibility = random.randint(1, 99)
        string = list('▬▬▬▬▬▬▬▬▬▬')
        string[compatibility // 10] = ':heart:'
        string = "[" + ''.join(string) + "]"
        embed = discord.Embed(title=f'Сравниваемые имена: {name} и {name2}.', description=f'Имечко: **{shipname}**\nСовместимость: **{compatibility}**% :heart:\n**{string}**')
        embed.color = discord.Color.random()
        await ctx.send(embed=embed)

    async def d1(self, ctx: commands.Context):
        await ctx.message.delete()
    async def s2(self, ctx: commands.Context, content):
        await ctx.send(' '.join(content))
    @commands.command()
    async def say(self, ctx: commands.Context, *content):
        if not content:
            await ctx.message.delete()
            return
        self.bot.loop.create_task(self.d1(ctx))
        self.bot.loop.create_task(self.s2(ctx, content))

    @commands.command()
    async def leave(self, ctx: commands.Context, *guildid):
        if ctx.author.id == self.bot.owner_id:
            if not guildid:
                msg = ''
                for i in self.bot.guilds:
                    msg += f'`{i}, {i.id}`\n'
                await ctx.send(embed = discord.Embed(title='Мои Сервера: ',description=msg, color=0x00ffff))
                return
            guildid = int(guildid[0])
            try:
                guild = self.bot.get_guild(guildid)
                if guild is not None:
                    await guild.leave()
                    await ctx.send(f"`Я покинула {guild.name}`")
                else:
                    await ctx.send("`Сервер не найден.`")
            except:
                await ctx.send("`Что то пошло не так...`")

    @commands.command()
    @has_permissions(administrator=True)
    async def vcm(self, ctx: commands.Context, *channel):
        ids = [self.bot.owner_id]
        done = False
        if not channel:
            await ctx.send("`s!vcm <channel_id | mention> заглушает всех в голосовом канале.`")
            return
        try:
            vc = self.bot.get_channel(int(str(channel[0]).replace("<#", '').replace(">", '')))
            if not vc: await ctx.send("`Канал не найден.`")
            if vc.guild.name != ctx.guild.name:
                await ctx.send("`Канал не найден.`")
                return
            for member in vc.members:
                if not int(member.id) in ids:
                    await member.edit(mute=True, reason="voice_channel_mute")
                    done = True
            if done:
                await ctx.send(f'`Все участники в канале {vc.name} заглушены.`')
            else:
                await ctx.send(f'`В канале {vc.name} нет участников, которых можно заглушить.`')
        except Exception:
            return

    async def d1(self, ctx: commands.Context):
        await ctx.message.delete()
    async def r2(self, ctx: commands.Context, content, message: discord.Message):
        await message.reply(content=' '.join(content))
    @commands.command(aliases = ['r', ])
    async def reply(self, ctx: commands.Context, *content):
        if not ctx.message.reference:
            return
        ref = ctx.message.reference
        message = self.bot.get_channel(ref.channel_id).get_partial_message(ref.message_id)
        self.bot.loop.create_task(self.d1(ctx))
        self.bot.loop.create_task(self.r2(ctx, content, message))

    @commands.command()
    @has_permissions(administrator=True)
    async def tickets(self, ctx: commands.Context, *args):
        if args:
            if args[0] == 'remove':
                txt = DataBase('tickets')
                res = txt.fetch('guildid', str(ctx.guild.id))
                if res['success'] == 'True':
                    def check(reaction, user):
                        return user == ctx.message.author and reaction.emoji == '💔'
                    try:
                        mess = await ctx.send('`Удалить систему жалоб?`')
                        await mess.add_reaction('💔')
                        await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
                        await mess.delete()
                    except asyncio.TimeoutError:
                        try:
                            await mess.delete()
                            return
                        except discord.errors.NotFound:
                            return
                    async with ctx.channel.typing():
                        value = res['value'].replace("'", '"').replace('\n', '')
                        value = json.loads(value)
                        category = discord.utils.get(ctx.guild.categories, id = int(value['catid']))
                        channel = self.bot.get_channel(int(value['channel_id']))
                        res = txt.remove('guildid', int(ctx.guild.id))
                        try:
                            await channel.delete()
                        except Exception:
                            pass
                        try:
                            await category.delete()
                        except Exception:
                            pass
                        try:
                            await ctx.send(f'`Система жалоб удалена участником`<@!{ctx.author.id}>`!`')
                            return
                        except discord.errors.NotFound:
                            return
                else:
                    embed = discord.Embed(description='`Система тикетов не найдена. s!tickets create`')
                    embed.color = 0x00ffff
                    await ctx.send(embed=embed)
            elif args[0] == 'create':
                done = False
                txt = DataBase('tickets')
                res = txt.fetch('guildid', str(ctx.guild.id))
                if res['success'] == 'True':
                    value = res['value'].replace("'", '"').replace('\n', '')
                    value = json.loads(value)
                    category = discord.utils.get(ctx.guild.categories, id = int(value['catid']))
                    channel = self.bot.get_channel(int(value['channel_id']))
                    if channel is not None and category is not None:
                        embed = discord.Embed(title='Tickets.', description=f'ticket-channel: <#{channel.id}> , {channel.id}\nticket-category: {category.name}, {category.id}')
                        embed.color = 0x00ffff
                        await ctx.send(embed=embed)
                        done = True
                        return
                if not done:
                    def check(reaction, user):
                        return user == ctx.message.author and reaction.emoji == '❤️'
                    try:
                        mess = await ctx.send('`Создать систему тикетов и жалоб?`')
                        await mess.add_reaction('❤️')
                        await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
                    except asyncio.TimeoutError:
                        try:
                            await mess.delete()
                            return
                        except discord.errors.NotFound:
                            return
                    try:
                        await mess.delete()
                    except discord.errors.NotFound:
                        pass
                    async with ctx.channel.typing():
                        category = await ctx.guild.create_category(name='-    Tickets    -', reason='tickets')
                        channel = await category.create_text_channel(name='Create Ticket', reason='tickets')
                        res = txt.add({'guildid': ctx.guild.id, 'catid': category.id, 'channel_id': channel.id, 'name': ctx.guild.name.replace("'", '')}, 'guildid')
                        await channel.send(">>> Если у вас есть жалоба или вопрос то этот канал для вас.\n**Убедительная просьба, не создавать тикеты просто так.**", view=Buttons())
                        await ctx.channel.send(f'`Система тикетов создана. Канал:`<#{channel.id}>')
            elif args[0] == 'perms':
                lst = []
                args = list(args)
                args.remove('perms')
                txt = DataBase('ticketsperms')
                for i in args:
                    arg = str(i).replace('<@&', '').replace('>', '')
                    lst.append(int(arg))
                res = txt.add({'guildid': ctx.guild.id, 'roles':lst}, 'guildid')
                text = '**Роли Обновлены:**\n'
                for i in lst:
                    text+=f'<@&{i}>\n'
                embed = discord.Embed(title='Права каналов для жалоб и тикетов.', description=text)
                embed.color = 0x00ffff
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Tickets", description="`<args: create/remove/perms>`", color=0x00ffff)
            await ctx.send(embed=embed)
# -----------------------------------------------------------------------------------------------------------
class Buttons_inChannel(discord.ui.View):
    ids = []
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
    @discord.ui.button(label="Закрыть Канал.", style=discord.ButtonStyle.gray)
    async def close(self, interaction:discord.Interaction, button: discord.ui.Button):
        if interaction.channel.id in self.ids or interaction.channel.id in _ids:
            await interaction.response.defer()
            return
        await interaction.response.send_message(content='`Канал удалится через 10 секунд...`')
        self.ids.append(interaction.channel.id)
        _ids.append(interaction.channel.id)
        pinid = await interaction.channel.pins()
        pinid = int(str(pinid[0].content).replace('>>> Ваш id: ', ''))
        member = await botik.fetch_user(pinid)
        await interaction.channel.set_permissions(member, send_messages=False)
        await asyncio.sleep(9)
        try:
            await interaction.channel.delete()
        except discord.errors.NotFound:
            return
        self.ids.remove(interaction.channel.id)
        _ids.remove(interaction.channel.id)
class Buttons(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
    @discord.ui.button(label="Жалоба", style=discord.ButtonStyle.red)
    async def jaloba(self, interaction:discord.Interaction, button: discord.ui.Button):
        txt = DataBase('tickets')
        res = txt.fetch('guildid', str(interaction.guild.id))['value']
        value = res.replace("'", '"').replace('\n', '')
        value = json.loads(value)
        category = discord.utils.get(interaction.guild.categories, id=value['catid'])
        await interaction.response.defer(ephemeral=True, thinking=True)
        for i in category.text_channels:
            channel = botik.get_channel(i.id)
            a = await channel.pins()
            for j, k in enumerate(a):
                if int(str(a[j].content).replace('>>> Ваш id: ', '')) == int(interaction.user.id):
                    await interaction.followup.send(content=f'Перейдите в канал <#{i.id}>.', ephemeral=True)
                    return
        channel = await interaction.guild.create_text_channel(f"Жалоба {interaction.user.name}", category=category)
        await channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await channel.set_permissions(target=interaction.user, view_channel=True)
        try:
            db = DataBase('ticketsperms')
            for i in db._getobjectsjson():
                if interaction.guild.id == int(i['guildid']):
                    for j in i['roles']:
                        role = interaction.guild.get_role(int(j))
                        await channel.set_permissions(role, view_channel=True, send_messages=True)
        except Exception:
            pass
        await interaction.followup.send(content=f'Канал <#{channel.id}> создан.', ephemeral=True)
        await channel.send(f'>>> <@!{interaction.user.id}>')
        message = await channel.send(f'>>> Ваш id: {interaction.user.id}')
        await message.pin()
        async for x in channel.history(limit=10):
            if x.content == '':
                await x.delete()
        message = await channel.send(f'>>> Жалоба была успешно создана.', view=Buttons_inChannel())
    @discord.ui.button(label="Тикет", style=discord.ButtonStyle.green)
    async def ticket(self, interaction:discord.Interaction, button: discord.ui.Button):
        txt = DataBase('tickets')
        res = txt.fetch('guildid', str(interaction.guild.id))['value']
        value = res.replace("'", '"').replace('\n', '')
        value = json.loads(value)
        category = discord.utils.get(interaction.guild.categories, id=value['catid'])
        await interaction.response.defer(ephemeral=True, thinking=True)
        for i in category.text_channels:
            a = await botik.get_channel(i.id).pins()
            for j, k in enumerate(a):
                if int(str(a[j].content).replace('>>> Ваш id: ', '')) == int(interaction.user.id):
                    await interaction.followup.send(content=f'Перейдите в канал <#{i.id}>.', ephemeral=True)
                    return           
        channel = await interaction.guild.create_text_channel(f"Тикет {interaction.user.name}", category=category)
        await channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await channel.set_permissions(interaction.user, view_channel=True)
        try:
            db = DataBase('ticketsperms')
            for i in db._getobjectsjson():
                if interaction.guild.id == int(i['guildid']):
                    for j in i['roles']:
                        role = interaction.guild.get_role(int(j))
                        await channel.set_permissions(role, view_channel=True, send_messages=True)
        except Exception:
            pass
        await interaction.followup.send(content=f'Канал <#{channel.id}> создан.', ephemeral=True)
        await channel.send(f'>>> <@!{interaction.user.id}>')
        message = await channel.send(f'>>> Ваш id: {interaction.user.id}')
        await message.pin()
        async for x in channel.history(limit=10):
            if x.content == '':
                await x.delete()
        message = await channel.send(f'>>> Тикет был успешно создан.', view=Buttons_inChannel())
# -----------------------------------------------------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(cmds(bot))