import discord, requests, json, datetime, os, asyncio, random, traceback, time, sys, emoji
from discord.ext import commands
from discord.utils import get
from discord.ext.commands import has_permissions
from Config.assets.database import MongoDB
from discord import app_commands
from Config.components import Reactions
# -----------------------------------------------------------------------------------------------------------
class cmds(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @has_permissions(administrator=True)
    @app_commands.command(name="reactroles", description='Выдача ролей по реакции.')
    async def reactions(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message('>>> Роли по реакции.\nВыберите нужную вам опцию:', view=Reactions(bot=self.bot), ephemeral=True)

    @commands.command()
    async def ping(self, ctx: commands.Context):
        ping1 = f"{str(round(self.bot.latency * 1000))} ms"
        embed = discord.Embed(title = "**Pong!**", description = "`" + ping1 + "`", color = 0xafdafc)
        await ctx.send(embed = embed)

    @commands.command()
    @has_permissions(administrator=True)
    async def logs(self, ctx: commands.Context, *args):
        try:
            if args[0] == 'add':
                res = self.bot.bd.fetch({'guildid': ctx.guild.id}, category='logs')
                if res['success'] == 'False':
                    channel = self.bot.get_channel(int(args[1].replace('<#', '').replace('>', '')))
                    if channel is not None and channel.guild.id == ctx.guild.id and str(channel.type) == 'text':
                        mess = await ctx.send(f'`Добавить систему логов?`')
                        await mess.add_reaction('❤️')
                        def check(reaction, user):
                            return user == ctx.message.author and reaction.emoji == '❤️'
                        try:
                            await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
                            res = self.bot.bd.add({'guildid': channel.guild.id, 'channel_id': channel.id}, category='logs')
                            if res['added'] == 'True':
                                await mess.edit(content=f'`Система логов добавлена. Канал:` <#{channel.id}>')
                            else:
                                await mess.edit(content=f'`Новый канал для системы логов:` <#{channel.id}>')
                            await mess.clear_reactions()
                            return
                        except asyncio.TimeoutError:
                            try:
                                await mess.delete()
                                return
                            except discord.errors.NotFound:
                                return
                    else:
                        await ctx.send('`Канал не найден среди текстовых каналов сервера.`')
                        return
                else:
                    channel = self.bot.get_channel(int(res['value']['channel_id']))
                    await ctx.send(f'`Система логов уже активна. Канал:`<#{channel.id}>')
                    return
            elif args[0] == 'remove':
                res = self.bot.bd.fetch({'guildid': ctx.guild.id}, category='logs')
                if res['success'] == 'True':
                    mess = await ctx.send(f'`Удалить Систему логов?`')
                    await mess.add_reaction('💔')
                    def check(reaction, user):
                        return user == ctx.message.author and reaction.emoji == '💔'
                    try:
                        await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
                        self.bot.bd.remove({'guildid': ctx.guild.id}, category='logs')
                        await mess.edit(content=f'`Система логов удалена пользователем` <@!{ctx.author.id}>')
                        await mess.clear_reactions()
                        return
                    except asyncio.TimeoutError:
                        try:
                            await mess.delete()
                            return
                        except discord.errors.NotFound:
                            return
                else:
                    await ctx.send('`Система логов не найдена.`')
        except Exception:
            print(traceback.format_exc())
            await ctx.send('`Что то пошло не так...`')

    @commands.command()
    @has_permissions(administrator=True)
    async def setprefix(self, ctx: commands.Context, prefix):
        def getprefix():
            res = self.bot.bd.fetch({'guildid': ctx.guild.id}, category='prefixes')
            if res['success'] == 'True':
                return res['value']['prefix'] == prefix
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
            self.bot.bd.add({'guildid': ctx.guild.id, 'prefix': f'{prefix}'}, check={'guildid': ctx.guild.id}, category='prefixes')
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
            a = self.bot.bd.remove({'voiceid': id}, category='voicemembers')
            guild = self.bot.get_guild(int(channel.guild.id))
            if a['done'] == 'True':
                await ctx.send(f'<#{channel.id}> `Убран из каналов статистики на сервере` **{guild.name}**')
            else:
                await ctx.send(f'`Канал не найден`')
            return
        id = int(str(args[0]).replace('<#', '').replace('>', ''))
        channel = self.bot.get_channel(id)
        if channel:
            info = self.bot.bd.add({'guildid': channel.guild.id, 'voiceid': id, 'name': str(channel.guild.name).replace(',', '').replace("'",'')}, {'guildid': ctx.guild.id}, category='voicemembers')
            if info['added'] == 'True':
                await ctx.send(f'`Канал успешно добавлен. Канал:` <#{channel.id}>')
                guild = self.bot.get_guild(int(channel.guild.id))
                await channel.edit(name=f"Участников: {guild.member_count}")
                return
            elif info['replaced'] == 'True':
                await ctx.send(f'`Канал успешно обновлен. Новый канал:` <#{channel.id}>')
                guild = self.bot.get_guild(int(channel.guild.id))
                await channel.edit(name=f"Участников: {guild.member_count}")
                return
        else:
            await ctx.send(f'`Канал не найден.`')

    @commands.command()
    async def help(self, ctx: commands.Context):
        com1 = '**Hypixel**:\n`s!link, s!unlink`\n`s!gtop, s!s`\n\n'
        com2 = '**Команды**:\n`s!reply, s!vcm`\n`s!say, s!ship`\n`s!vc-members <remove>\ns!tickets <create/remove/perms>`\n `s!reaction-roles <view (message_id / all)/remove (message_id)>`\n`s!setprefix, s!ping`'
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
                res = self.bot.bd.fetch({'guildid': ctx.guild.id}, category='tickets')
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
                        value = res['value']
                        category = discord.utils.get(ctx.guild.categories, id = int(value['catid']))
                        channel = self.bot.get_channel(int(value['channel_id']))
                        res = self.bot.bd.remove({'guildid': int(ctx.guild.id)}, category='tickets')
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
                res = self.bot.bd.fetch({'guildid': ctx.guild.id}, category='tickets')
                if res['success'] == 'True':
                    value = res['value']
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
                        channel.set_permissions(channel.guild.default_role, send_messages=False)
                        res = self.bot.bd.add({'guildid': ctx.guild.id, 'catid': category.id, 'channel_id': channel.id, 'name': ctx.guild.name.replace("'", '')}, check={'guildid': ctx.guild.id}, category='tickets')
                        await channel.send(">>> Если у вас есть жалоба или вопрос то этот канал для вас.\n**Убедительная просьба, не создавать тикеты просто так.**", view=Buttons(bot=self.bot))
                        await ctx.channel.send(f'`Система тикетов создана. Канал:`<#{channel.id}>')
            elif args[0] == 'perms':
                lst = []
                args = list(args)
                args.remove('perms')
                for i in args:
                    arg = str(i).replace('<@&', '').replace('>', '')
                    lst.append(int(arg))
                res = self.bot.bd.add({'guildid': ctx.guild.id, 'roles':lst}, check={'guildid': ctx.guild.id}, category='ticketsperms')
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
        async def c1(channel):
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
    def __init__(self, *, bot: commands.Bot, timeout=None):
        super().__init__(timeout=timeout)
        self.bot = bot
    @discord.ui.button(label="Жалоба", style=discord.ButtonStyle.red)
    async def jaloba(self, interaction:discord.Interaction, button: discord.ui.Button):
        res = self.bot.bd.fetch({'guildid': interaction.guild.id}, category='tickets')['value']
        value = res
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
        async def p1(channel):
            await channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await channel.set_permissions(target=interaction.user, view_channel=True)
            try:
                for i in self.bot.bd.fetch({}, mode='all', category='ticketsperms')['value']:
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
        message = await channel.send(f'>>> Жалоба была успешно создана.', view=Buttons_inChannel(bot=self.bot))
    @discord.ui.button(label="Тикет", style=discord.ButtonStyle.green)
    async def ticket(self, interaction:discord.Interaction, button: discord.ui.Button):
        res = self.bot.bd.fetch({'guildid': interaction.guild.id}, category='tickets')['value']
        value = res
        category = discord.utils.get(interaction.guild.categories, id=value['catid'])
        await interaction.response.defer(ephemeral=True, thinking=True)
        for i in category.text_channels:
            a = await self.bot.get_channel(i.id).pins()
            for j, k in enumerate(a):
                if int(str(a[j].content).replace('>>> Ваш id: ', '')) == int(interaction.user.id):
                    await interaction.followup.send(content=f'Перейдите в канал <#{i.id}>.', ephemeral=True)
                    return           
        channel = await interaction.guild.create_text_channel(f"Тикет {interaction.user.name}", category=category)
        async def p1(channel):
            await channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await channel.set_permissions(target=interaction.user, view_channel=True)
            try:
                for i in self.bot.bd.fetch({}, mode='all', category='ticketsperms')['value']:
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