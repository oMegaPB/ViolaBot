import time
import discord, requests, json, datetime, os, asyncio, traceback
from discord.ext import commands, tasks
from discord.ext.commands.errors import CommandNotFound, MemberNotFound
from discord.ext.commands import has_permissions, MissingPermissions, MissingRequiredArgument, CommandInvokeError
from Cogs.cmds import Buttons, Buttons_inChannel
from Config.core import Viola

class events(commands.Cog):
    def __init__(self, bot: Viola):
        self.bot = bot
        self.entrys = []
    
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
    
    async def tickets_renew(self):
        all = await self.bot.bd.rows(mode='list', category='tickets')
        for i in all.value:
            id = int(i['channel_id'])
            channel = self.bot.get_channel(id)
            if channel is not None:
                async for message in channel.history(limit=10, oldest_first=True):
                    if ">>> Если у вас есть жалоба или вопрос то этот канал для вас." in message.content:
                        try:
                            await message.edit(view=Buttons(bot=self.bot))
                        except discord.errors.Forbidden:
                            pass
            category = self.bot.get_channel(int(i['catid']))
            if category is not None:
                for k in category.text_channels:
                    channel = self.bot.get_channel(k.id)
                    async for message in channel.history(limit=10, oldest_first=True):
                        if message.content == '>>> Тикет был успешно создан.' or message.content =='>>> Жалоба была успешно создана.':
                            try:
                                await message.edit(view=Buttons_inChannel(bot=self.bot))
                            except discord.errors.Forbidden:
                                pass
    @tasks.loop(seconds=250)
    async def update_VoiceChannel_members(self):
        all = await self.bot.bd.rows(mode='list', category='voicemembers')
        for i in all.value:
            channel = self.bot.get_channel(int(i['voiceid']))
            guild = self.bot.get_guild(int(i['guildid']))
            try:
                await channel.edit(name=f"Участников: {guild.member_count}")
            except Exception:
                pass
            await asyncio.sleep(3)

    @commands.Cog.listener()
    async def on_ready(self):
        # await self.bot.sync()
        await self.bot.load_extension("Cogs.music")
        self.update_VoiceChannel_members.start()
        await self.tickets_renew()
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{self.bot.user.name}/INFO]: Logged in as {self.bot.user.name}.")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{self.bot.user.name}/INFO]: Bot Owner: {self.bot.get_user(self.bot.owner_id).name}")
        print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] [{self.bot.user.name}/INFO]: Bot started at {time.time() - self.bot.time} seconds.')
        print('-------------------------------------------')
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        print(member, 'joined', member.guild.name)
        res = await self.bot.bd.fetch({'guildid': member.guild.id, 'memberid': member.id}, category='joined')
        if not res.status:
            await self.bot.bd.add({'guildid': member.guild.id, 'memberid': member.id, 'time': int(member.joined_at.timestamp())}, category='joined')
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        print(member, 'leaved', member.guild.name)
        args = await self.getmarryinfo(member)
        if args is not None:
            await self.bot.bd.remove({'guildid': member.guild.id, 'memberid': member.id}, category='marry')
            await self.bot.bd.remove({'guildid': member.guild.id, 'partnerid': member.id}, category='marry')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.raw_models.RawReactionActionEvent):
        res = await self.bot.bd.fetch({'message_id': payload.message_id}, mode='all', category='reactroles')
        try:
            for i in res.value:
                if i['reaction'] == payload.emoji.name and i['channel_id'] == payload.channel_id:
                    role = discord.utils.get(self.bot.get_guild(payload.guild_id).roles, id=int(i['role_id']))
                    try:
                        await payload.member.add_roles(role, reason='Роли за реакцию.')
                    except discord.errors.Forbidden:
                        pass
                await asyncio.sleep(1)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.raw_models.RawReactionActionEvent):
        res = await self.bot.bd.fetch({'message_id': payload.message_id}, mode='all', category='reactroles')
        try:
            for i in res.value:
                if i['reaction'] == payload.emoji.name and i['channel_id'] == payload.channel_id:
                    role = discord.utils.get(self.bot.get_guild(payload.guild_id).roles, id=int(i['role_id']))
                    try:
                        guild = self.bot.get_guild(payload.guild_id)
                        member = guild.get_member(payload.user_id)
                        await member.remove_roles(role, reason='Роли за реакцию.')
                    except discord.errors.Forbidden:
                        return
                await asyncio.sleep(1)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.member.VoiceState, after: discord.member.VoiceState):
        # <AuditLogEntry id=998929831263731784 action=AuditLogAction.member_disconnect user=<Member id=728165963480170567 name='MegaWatt_' discriminator='1114' bot=False nick=None guild=<Guild id=742394556405907457 name="Viola's house" shard_id=0 chunked=True member_count=13>>>
        again = False
        if before.channel is None and after.channel is not None:
            print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {member.name} зашел в канал {after.channel.name} | {after.channel.guild.name}')
        elif before.channel is not None and after.channel is None:
            print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {member.name} покинул канал {before.channel.name} | {before.channel.guild.name}')
            res = await self.bot.bd.fetch({'guildid': member.guild.id}, category='logs')
            if res.status:
                value = res.value
                channel = self.bot.get_channel(int(value['channel_id']))
                async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_disconnect):
                    app = False
                    for i in self.entrys:
                        if str(entry.id) in i.keys():
                            app = True
                            if i[str(entry.id)] != str(entry.extra.count):
                                i[str(entry.id)] = str(entry.extra.count)
                                again = True
                    if not app:
                        self.entrys.append({str(entry.id): str(entry.extra.count)})
                    old = False
                    a = round(entry.created_at.timestamp())
                    b = round(datetime.datetime.utcnow().timestamp())
                    if b - a > 25:
                        old = True
                    if entry.user.id != member.id:
                        if ((not old) or again) and not ((not old) and again):
                            embed = discord.Embed(title='Отключение из голосового канала.', description=f'`{entry.user.name}#{entry.user.discriminator}` отключил `{member.name}#{member.discriminator}` из канала <#{before.channel.id}>')
                            embed.color = 0x00ffff
                            try:
                                embed.set_footer(text=f'{member.guild.name}', icon_url=f'{member.guild.icon.url}')
                            except Exception:
                                embed.set_footer(text=f'{member.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
                            await channel.send(embed=embed)
                return
        elif before.channel is not None and after.channel is not None:
            if before.channel.name == after.channel.name:
                return
            print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {member.name} перешёл в канал {after.channel.name} из {before.channel.name} | {before.channel.guild.name}')

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, CommandNotFound):
            # await ctx.send("`Неизвестная команда. Используйте s!help Для списка команд.`")
            return
        elif isinstance(error, MissingPermissions):
            await ctx.channel.send(embed=discord.Embed(title='Error', description=f'Вам не хватает прав для данного действия.\nВам нужны права:(**{error.missing_permissions[0]}**)', color=discord.Color.red()))
        elif isinstance(error, MissingRequiredArgument):
            await ctx.send(f'`Не хватает аргументов. Укажите аргумент:` **{error.param}**')
        elif isinstance(error, MemberNotFound):
            embed = discord.Embed(color=discord.Color.red())
            embed.title = 'Ошибка.'
            embed.description = 'Участник не найден.'
            await ctx.message.reply(embed=embed)
        elif isinstance(error, commands.CommandError):
            await ctx.message.reply(error)
        else:
            raise error
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        # print(interaction)
        return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.bot:
            ctx = await self.bot.get_context(message)
            if not message.guild:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [Viola/INFO]: {message.author} Написал(а) мне в лс: {message.content}")
                return
            if 'await' in message.content:
                if message.author.id == self.bot.owner_id:
                    if message.reference:
                        msg = await message.channel.fetch_message(message.reference.message_id)
                        member = msg.author
                        try:
                            await eval(message.content.replace('await ',''))
                        except Exception as e:
                            await message.channel.send(e)
                    else:
                        try:
                            await eval(message.content.replace('await ',''))
                        except Exception as e:
                            await message.channel.send(e)
                    return
            if ctx.command is not None:
                return
            res = await self.bot.bd.fetch({'guildid': message.guild.id, 'memberid': message.author.id}, category='messages')
            if not res.status:
                await self.bot.bd.add({'guildid': message.guild.id, 'memberid': message.author.id, 'amount': 1}, category='messages')
                return
            else:
                msgs = res.value['amount']
                level1 = self.bot.GetLevel(msgs)
                await self.bot.bd.remove(res.value, category='messages')
                await self.bot.bd.add({'guildid': message.guild.id, 'memberid': message.author.id, 'amount': msgs+1}, category='messages')
                res = await self.bot.bd.fetch({'guildid': message.guild.id, 'memberid': message.author.id}, category='messages')
                msgs = res.value['amount']
                level2 = self.bot.GetLevel(msgs)
                if level1 < level2:
                    await message.reply(f'Ура! {message.author.mention} только что поднял свой уровень до **{level2[0]}**!')

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        res = await self.bot.bd.fetch({'guildid': message.guild.id}, category='logs')
        if res.status:
            value = res.value
            channel = self.bot.get_channel(int(value['channel_id']))
            # <AuditLogEntry id=995728596524085290 action=AuditLogAction.message_delete user=<Member id=728165963480170567 name='MegaWatt_' discriminator='1114' bot=False nick='Микроволновка' guild=<Guild id=506049013460631552 name='🌸 DG × 2022 ✨' shard_id=None chunked=True member_count=62>>>
            async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
                old = False
                a = round(entry.created_at.timestamp())
                b = round(datetime.datetime.utcnow().timestamp())
                if b - a > 10850:
                    old = True
                if not int(message.channel.id) == channel.id and int(value['guildid']) == message.guild.id:
                    if message.attachments:
                        description = ''
                        for i, j in enumerate(message.attachments):
                            description += message.attachments[i].url
                        embed = discord.Embed(description=description, color=discord.Color.red())
                    else:
                        description = message.content
                        if description == '':
                            description = '`attachment`'
                        embed = discord.Embed(description=description, color=discord.Color.red())
                        try:
                            embed.set_footer(text=f'{message.guild.name}', icon_url=f'{message.guild.icon.url}')
                        except Exception:
                            embed.set_footer(text=f'{message.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
                    if not old:
                        if entry.user.name != message.author.name:
                            await channel.send(f':x: `[{datetime.datetime.now().strftime("%H:%M:%S")}]` **{entry.user.name}**#{entry.user.discriminator} Удалил сообщение от **{message.author.name}**#{message.author.discriminator} в канале <#{message.channel.id}>', embed=embed)
                        else:
                            await channel.send(f':x: `[{datetime.datetime.now().strftime("%H:%M:%S")}]` **{message.author.name}**#{message.author.discriminator} удалил свое сообщение в канале <#{message.channel.id}>', embed=embed) 
                    else:
                        await channel.send(f':x: `[{datetime.datetime.now().strftime("%H:%M:%S")}]` Cообщение от **{message.author.name}**#{message.author.discriminator} удалено в канале <#{message.channel.id}>', embed=embed) 

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.message.Message, after: discord.message.Message):
        if before.author.bot:
            return
        try:
            res = await self.bot.bd.fetch({'guildid': before.guild.id}, category='logs')
            if res.status:
                value = res.value
                channel = self.bot.get_channel(int(value['channel_id']))
                if before.content != after.content:
                    if not int(before.channel.id) == channel.id and int(value['guildid']) == before.guild.id:
                        if before.content == '':
                            before.content += '`attachment`'
                        description = '**Было:**\n' + before.content + '\n\n' + '**Стало:**\n' + after.content
                        embed = discord.Embed(description=description, color=discord.Color.gold())
                        try:
                            embed.set_footer(text=f'{after.guild.name}', icon_url=f'{after.guild.icon.url}')
                        except Exception:
                            embed.set_footer(text=f'{after.guild.name}', icon_url=f'{self.bot.user.avatar.url}')
                        await channel.send(f'`[{datetime.datetime.now().strftime("%H:%M:%S")}]` **{before.author.name}**#{before.author.discriminator} Изменил свое сообщение в канале <#{before.channel.id}>', embed=embed)
        except Exception:
            pass
async def setup(bot: commands.Bot):
    await bot.add_cog(events(bot))