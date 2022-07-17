import discord, requests, json, datetime, os, asyncio, random, traceback, time, sys
from discord.ext import commands
from discord.ext.commands import has_permissions
from Config.assets.database import DataBase
_ids = []
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

    @commands.command()
    async def ping(self, ctx: commands.Context):
        ping1 = f"{str(round(self.bot.latency * 1000))} ms"
        embed = discord.Embed(title = "**Pong!**", description = "`" + ping1 + "`", color = 0xafdafc)
        await ctx.send(embed = embed)

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
        com1 = "`s!link <ign>`/`s!unlink`: Link/Unlink your account.\n`s!gtop <*day> <name>`: Display guild top by exp.\n`s!s <*ign>`: Showing your hypixel stats.\n`s!reply <content>`: Replying to message.\n`s!vcm <channel_id | mention>`: Mutes everyone in voice channel\n"
        com2 = "`s!say <content>` sends content in chat\n`s!ship <user mention | name> <user mention | name>`: fun command.\n`s!vc-members <channel_id | mention> OR remove <channel_id | mention>`"
        com3 = "`s!tickets <create/remove>`: Система жалоб и тикетов."
        embed = discord.Embed(title="Help", description=com1+com2+com3, color=discord.Color.green())
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

    @commands.command(aliases = ['r', ])
    async def reply(self, ctx: commands.Context, *content):
        await ctx.message.delete()
        if not ctx.message.reference:
            return
        ref = ctx.message.reference
        message = self.bot.get_channel(ref.channel_id).get_partial_message(ref.message_id)
        await message.reply(content=' '.join(content))

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