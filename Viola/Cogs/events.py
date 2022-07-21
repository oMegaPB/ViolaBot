import discord, requests, json, datetime, os, asyncio, traceback
from discord.ext import commands, tasks
from discord.ext.commands.errors import CommandNotFound
from discord.ext.commands import has_permissions, MissingPermissions, MissingRequiredArgument
from Cogs.cmds import Buttons, Buttons_inChannel
from Config.core import Viola

entrys_ = []

class events(commands.Cog):
    def __init__(self, bot: Viola):
        self.bot = bot

    async def tickets_renew(self):
            for i in self.bot.bd.fetch({}, mode='all', category='tickets')['value']:
                id = int(i['channel_id'])
                channel = self.bot.get_channel(id)
                if channel is not None:
                    async for message in channel.history(limit=10, oldest_first=True):
                        if ">>> Если у вас есть жалоба или вопрос то этот канал для вас." in message.content:
                            try:
                                await message.edit(content=message.content, view=Buttons(bot=self.bot))
                            except discord.errors.Forbidden:
                                pass
                category = self.bot.get_channel(int(i['catid']))
                if category is not None:
                    for k in category.text_channels:
                        channel = self.bot.get_channel(k.id)
                        async for message in channel.history(limit=10, oldest_first=True):
                            if message.content == '>>> Тикет был успешно создан.' or message.content =='>>> Жалоба была успешно создана.':
                                try:
                                    await message.edit(content=message.content, view=Buttons_inChannel(bot=self.bot))
                                except discord.errors.Forbidden:
                                    pass
    @tasks.loop(seconds=360)
    async def update_VoiceChannel_members(self):
        for i in self.bot.bd.fetch({}, mode='all', category='voicemembers')['value']:
            channel = self.bot.get_channel(int(i['voiceid']))
            guild = self.bot.get_guild(int(i['guildid']))
            try:
                await channel.edit(name=f"Участников: {guild.member_count}")
            except Exception:
                pass
            await asyncio.sleep(3)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.sync()
        self.update_VoiceChannel_members.start()
        await self.tickets_renew()
        print('-------------------------------------------')
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{self.bot.user.name}/INFO]: Logged in as {self.bot.user.name}.")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{self.bot.user.name}/INFO]: Bot Owner: {self.bot.get_user(self.bot.owner_id).name}")
        print('-------------------------------------------')
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.raw_models.RawReactionActionEvent):
        res = self.bot.bd.fetch({'message_id': payload.message_id}, mode='all', category='reactroles')
        try:
            for i in res['value']:
                if i['reaction'] == payload.emoji.name and i['channel_id'] == payload.channel_id:
                    role = discord.utils.get(self.bot.get_guild(payload.guild_id).roles, id=int(i['role_id']))
                    try:
                        await payload.member.add_roles(role, reason='Роли за реакцию.')
                    except discord.errors.Forbidden:
                        channel = self.bot.get_channel(int(i['channel_id']))
                        try:
                            await channel.send(embed=discord.Embed(description=f'Боту не хватает прав выдать роль <@&{i["role_id"]}>!!!', color=0x00ffff))
                        except Exception:
                            pass
                await asyncio.sleep(1)
        except Exception:
            return

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.raw_models.RawReactionActionEvent):
        res = self.bot.bd.fetch({'message_id': payload.message_id}, mode='all', category='reactroles')
        try:
            for i in res['value']:
                if i['reaction'] == payload.emoji.name and i['channel_id'] == payload.channel_id:
                    role = discord.utils.get(self.bot.get_guild(payload.guild_id).roles, id=int(i['role_id']))
                    try:
                        guild = self.bot.get_guild(payload.guild_id)
                        member = guild.get_member(payload.user_id)
                        await member.remove_roles(role, reason='Роли за реакцию.')
                    except discord.errors.Forbidden:
                        channel = self.bot.get_channel(int(i['channel_id']))
                        try:
                            await channel.send(embed=discord.Embed(description=f'Боту не хватает прав забрать роль <@&{i["role_id"]}>!!!', color=0x00ffff))
                        except Exception:
                            pass
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
            res = self.bot.bd.fetch({'guildid': member.guild.id}, category='logs')
            if res['success'] == 'True':
                value = res['value']
                channel = self.bot.get_channel(int(value['channel_id']))
                async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_disconnect):
                    app = False
                    for i in entrys_:
                        if str(entry.id) in i.keys():
                            app = True
                            if i[str(entry.id)] != str(entry.extra.count):
                                i[str(entry.id)] = str(entry.extra.count)
                                again = True
                    if not app:
                        entrys_.append({str(entry.id): str(entry.extra.count)})
                    old = False
                    a = round(entry.created_at.timestamp())
                    b = round((datetime.datetime.utcnow() + datetime.timedelta(hours=3)).timestamp())
                    print(a)
                    print(b)
                    print(b-a)
                    if b - a > 50:
                        old = True
                    if entry.user.id != member.id:
                        if (not old) or again:
                            embed = discord.Embed(title='Отключение из голосового канала.', description=f'`{entry.user.name}#{entry.user.discriminator}` отключил `{member.name}#{member.discriminator}` из канала <#{before.channel.id}>')
                            embed.color = 0x00ffff
                            embed.set_footer(text=f'{member.guild.name}', icon_url=f'{member.guild.icon}')
                            await channel.send(embed=embed)
                return
        elif before.channel is not None and after.channel is not None:
            if before.channel.name == after.channel.name:
                return
            print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {member.name} перешёл в канал {after.channel.name} из {before.channel.name} | {before.channel.guild.name}')

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, CommandNotFound):
            await ctx.send("`Неизвестная команда. Используйте s!help Для списка команд.`")
        elif isinstance(error, MissingPermissions):
            await ctx.send(f'`Вам не хватает прав.`(`{error.missing_permissions[0]}`)')
        elif isinstance(error, MissingRequiredArgument):
            await ctx.send(f'`Не хватает аргументов. Укажите аргумент:` **{error.param}**')
        else:
            raise error

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if str(message.author.bot) == 'False':
            if not message.guild:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [Viola/INFO]: {message.author} Написал(а) мне в лс: {message.content}")
                return
            if message.content == "<@786591502968422500>":
                async with message.channel.typing():
                    await asyncio.sleep(3)
                    await message.reply(f'Господин ответит, когда освободится ( ͡°³ ͡°)')
            elif '!sex' in message.content:
                async with message.channel.typing():
                    await asyncio.sleep(1)
                    await message.reply(f'Готовь попочку :pleading_face: :heart_eyes: ')
            elif message.content == '<@924357517306380378>':
                self.bot.bd.fetch({})

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        res = self.bot.bd.fetch({'guildid': message.guild.id}, category='logs')
        if res['success'] == 'True':
            value = res['value']
            channel = self.bot.get_channel(int(value['channel_id']))
            # <AuditLogEntry id=995728596524085290 action=AuditLogAction.message_delete user=<Member id=728165963480170567 name='MegaWatt_' discriminator='1114' bot=False nick='Микроволновка' guild=<Guild id=506049013460631552 name='🌸 DG × 2022 ✨' shard_id=None chunked=True member_count=62>>>
            async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
                old = False
                a = round(entry.created_at.timestamp())
                b = round((datetime.datetime.utcnow() + datetime.timedelta(hours=3)).timestamp())
                if b - a > 50:
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
                    embed.set_footer(text=f'{message.guild.name}', icon_url=f'{message.guild.icon}')
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
            res = self.bot.bd.fetch({'guildid': before.guild.id}, category='logs')
            if res['success'] == 'True':
                value = res['value']
                channel = self.bot.get_channel(int(value['channel_id']))
                if before.content != after.content:
                    if not int(before.channel.id) == channel.id and int(value['guildid']) == before.guild.id:
                        if before.content == '':
                            before.content += '`attachment`'
                        description = before.content + '  --->  ' + after.content
                        embed = discord.Embed(description=description, color=discord.Color.gold())
                        embed.set_footer(text=f'{after.guild.name}', icon_url=f'{after.guild.icon}')
                        await channel.send(f'`[{datetime.datetime.now().strftime("%H:%M:%S")}]` **{before.author.name}**#{before.author.discriminator} Изменил свое сообщение в канале <#{before.channel.id}>', embed=embed)
        except Exception:
            pass
async def setup(bot: commands.Bot):
    await bot.add_cog(events(bot))