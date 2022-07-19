import discord, requests, json, datetime, os, asyncio, traceback
from discord.ext import commands, tasks
from discord.ext.commands.errors import CommandNotFound
from discord.ext.commands import has_permissions, MissingPermissions, MissingRequiredArgument
from Config.assets.database import DataBase
from Cogs.cmds import Buttons, Buttons_inChannel

class events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def tickets_renew(self):
            txt = DataBase('tickets')
            for i in txt._getobjectsjson():
                id = int(i['channel_id'])
                channel = self.bot.get_channel(id)
                if channel is not None:
                    async for message in channel.history(limit=10, oldest_first=True):
                        if ">>> Если у вас есть жалоба или вопрос то этот канал для вас." in message.content:
                            await message.edit(content=message.content, view=Buttons())
                category = self.bot.get_channel(int(i['catid']))
                if category is not None:
                    for k in category.text_channels:
                        channel = self.bot.get_channel(k.id)
                        async for message in channel.history(limit=10, oldest_first=True):
                            if message.content == '>>> Тикет был успешно создан.' or message.content =='>>> Жалоба была успешно создана.':
                                await message.edit(content=message.content, view=Buttons_inChannel())

    @tasks.loop(seconds=360)
    async def update_VoiceChannel_members(self):
        txt = DataBase('voicemembers')
        for i in txt._getobjectsjson():
            channel = self.bot.get_channel(int(i['voiceid']))
            guild = self.bot.get_guild(int(i['guildid']))
            try:
                await channel.edit(name=f"Участников: {guild.member_count}")
            except Exception:
                pass
            await asyncio.sleep(3)

    @commands.Cog.listener()
    async def on_ready(self):
        self.update_VoiceChannel_members.start()
        await self.tickets_renew()
        print('-------------------------------------------')
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{self.bot.user.name}/INFO]: Logged in as {self.bot.user.name}.")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{self.bot.user.name}/INFO]: Bot Owner: {self.bot.get_user(self.bot.owner_id).name}")
        print('-------------------------------------------')
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Visual Studio Code."))
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.raw_models.RawReactionActionEvent):
        txt = DataBase('reactroles')
        res = txt.fetchl('message_id', payload.message_id)
        try:
            for i in res['value']:
                args = json.loads(i.replace("'", '"').replace('\n', ''))
                if args['reaction'] == payload.emoji.name and args['channel_id'] == payload.channel_id:
                    role = discord.utils.get(self.bot.get_guild(payload.guild_id).roles, id=int(args['role_id']))
                    try:
                        await payload.member.add_roles(role, reason='Роли за реакцию.')
                    except discord.errors.Forbidden:
                        channel = self.bot.get_channel(int(args['channel_id']))
                        try:
                            await channel.send(embed=discord.Embed(description=f'Боту не хватает прав выдать роль <@&{args["role_id"]}>!!!', color=0x00ffff))
                        except Exception:
                            pass
                await asyncio.sleep(1)
        except Exception:
            return

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.raw_models.RawReactionActionEvent):
        txt = DataBase('reactroles')
        res = txt.fetchl('message_id', payload.message_id)
        try:
            for i in res['value']:
                args = json.loads(i.replace("'", '"').replace('\n', ''))
                if args['reaction'] == payload.emoji.name and args['channel_id'] == payload.channel_id:
                    role = discord.utils.get(self.bot.get_guild(payload.guild_id).roles, id=int(args['role_id']))
                    try:
                        guild = self.bot.get_guild(payload.guild_id)
                        member = guild.get_member(payload.user_id)
                        await member.remove_roles(role, reason='Роли за реакцию.')
                    except discord.errors.Forbidden:
                        channel = self.bot.get_channel(int(args['channel_id']))
                        try:
                            await channel.send(embed=discord.Embed(description=f'Боту не хватает прав забрать роль <@&{args["role_id"]}>!!!', color=0x00ffff))
                        except Exception:
                            pass
                await asyncio.sleep(1)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.member.VoiceState, after: discord.member.VoiceState):
        # <AuditLogEntry id=998929831263731784 action=AuditLogAction.member_disconnect user=<Member id=728165963480170567 name='MegaWatt_' discriminator='1114' bot=False nick=None guild=<Guild id=742394556405907457 name="Viola's house" shard_id=0 chunked=True member_count=13>>>
        if before.channel is None and after.channel is not None:
            print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {member.name} зашел в канал {after.channel.name} | {after.channel.guild.name}')
        elif before.channel is not None and after.channel is None:
            print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {member.name} покинул канал {before.channel.name} | {before.channel.guild.name}')
            txt = DataBase('msglogs')
            res = txt.fetch('guildid', member.guild.id)
            if res['success'] == 'True':
                value = json.loads(res['value'].replace("'", '"').replace("\n", ''))
                channel = self.bot.get_channel(int(value['channel_id']))
                async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_disconnect):
                    if entry.user.id != member.id:
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

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        txt = DataBase('msglogs')
        res = txt.fetch('guildid', message.guild.id)
        if res['success'] == 'True':
            value = json.loads(res['value'].replace("'", '"').replace("\n", ''))
            channel = self.bot.get_channel(int(value['channel_id']))
            # <AuditLogEntry id=995728596524085290 action=AuditLogAction.message_delete user=<Member id=728165963480170567 name='MegaWatt_' discriminator='1114' bot=False nick='Микроволновка' guild=<Guild id=506049013460631552 name='🌸 DG × 2022 ✨' shard_id=None chunked=True member_count=62>>>
            async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
                if not int(message.channel.id) == channel.id and int(value['guildid']) == message.guild.id:
                    if message.attachments:
                        description = ''
                        for i, j in enumerate(message.attachments):
                            description += message.attachments[i].url
                        embed = discord.Embed(description=description, color=discord.Color.red())
                    else:
                        description = message.content
                        embed = discord.Embed(description=description, color=discord.Color.red())
                    embed.set_footer(text=f'{message.guild.name}', icon_url=f'{message.guild.icon}')
                    await channel.send(f':x: `[{datetime.datetime.now().strftime("%H:%M:%S")}]` **{entry.user.name}**#{entry.user.discriminator} Удалил сообщение от **{message.author.name}**#{message.author.discriminator} в канале <#{message.channel.id}>', embed=embed)
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.message.Message, after: discord.message.Message):
        txt = DataBase('msglogs')
        res = txt.fetch('guildid', before.guild.id)
        if res['success'] == 'True':
            value = json.loads(res['value'].replace("'", '"').replace("\n", ''))
            channel = self.bot.get_channel(int(value['channel_id']))
            if before.content != after.content and before.author != after.author:
                if not int(before.channel.id) == channel.id and int(value['guildid']) == before.guild.id:
                    if before.content == '':
                        before.content += '`attachment`'
                    description = before.content + '  --->  ' + after.content
                    embed = discord.Embed(description=description, color=discord.Color.gold())
                    embed.set_footer(text=f'{after.guild.name}', icon_url=f'{after.guild.icon}')
                    await channel.send(f'`[{datetime.datetime.now().strftime("%H:%M:%S")}]` **{before.author.name}**#{before.author.discriminator} Изменил свое сообщение в канале <#{before.channel.id}>', embed=embed)
            
async def setup(bot: commands.Bot):
    await bot.add_cog(events(bot))