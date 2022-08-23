import discord, requests, json, datetime, os, asyncio, traceback
from discord.ext import commands, tasks
from typing import List, Dict, Any, Optional
from discord.ext.commands.errors import CommandNotFound, MemberNotFound, DisabledCommand
from discord.ext.commands import has_permissions, MissingPermissions, MissingRequiredArgument
from Config.components import ViolaEmbed
from Config.core import Viola

class events(commands.Cog):
    def __init__(self, bot: Viola) -> None:
        self.bot = bot
        self.entrys = [] # audit log entrys for channel disconnect purposes
        self.buffer: List[Dict[str, Any]] = [] # buffer for next voicetime database update
    
    @tasks.loop(seconds=1)
    async def update_buffer(self) -> None:
        for x in self.buffer:
            prevamount = x['amount'] + 1
            self.buffer.remove(x)
            for y in await self.bot.get_all_voice_members():
                if x['memberid'] == y.id:
                    self.buffer.append({'memberid': x['memberid'], 'guildid': x['guildid'], 'amount': prevamount})
    
    @tasks.loop(seconds=15)
    async def update_db_from_buffer(self) -> None:
        for j, x in enumerate(self.buffer):
            res = await self.bot.bd.fetch({'guildid': x['guildid'], 'memberid': x['memberid']}, category='voice')
            self.buffer.pop(j)
            self.buffer.append({'memberid': x['memberid'], 'guildid': x['guildid'], 'amount': 0})
            if res.status:
                amount = res.value['amount'] + x['amount']
                await self.bot.bd.remove({'guildid': x['guildid'], 'memberid': x['memberid']}, category='voice')
                await self.bot.bd.add({'guildid': x['guildid'], 'memberid': x['memberid'], 'amount': amount}, category='voice') 
    
    async def start_all_tasks(self) -> None:
        for x in await self.bot.get_all_voice_members():
            self.buffer.append({'memberid': x.id, 'guildid': x.guild.id, 'amount': 0})
        self.update_buffer.start()
        self.update_db_from_buffer.start()

    @commands.Cog.listener()
    async def on_socket_raw_send(self, payload: str):
        return
    
    @commands.Cog.listener()
    async def on_socket_raw_receive(self, payload: str):
        return
    
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.start_all_tasks()
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [{self.bot.user.name}/INFO]: Logged in as {self.bot.user.name}.")
        print('-------------------------------------------')
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        print(member, 'joined', member.guild.name)
        res = await self.bot.bd.fetch({'guildid': member.guild.id, 'memberid': member.id}, category='joined')
        if not res.status:
            await self.bot.bd.add({'guildid': member.guild.id, 'memberid': member.id, 'time': int(member.joined_at.timestamp())}, category='joined')
        channel = await self.bot.get_voicestats_channel(member.guild.id)
        if channel is not None:
            await channel.edit(name=f"Участников: {member.guild.member_count}")

    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        print(member, 'leaved', member.guild.name)
        args = await self.bot.get_marry_info(member)
        if args is not None:
            await self.bot.bd.remove({'guildid': member.guild.id, 'memberid': member.id}, category='marry')
            await self.bot.bd.remove({'guildid': member.guild.id, 'partnerid': member.id}, category='marry')
        channel = await self.bot.get_voicestats_channel(member.guild.id)
        if channel is not None:
            await channel.edit(name=f"Участников: {member.guild.member_count}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.raw_models.RawReactionActionEvent) -> None:
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
    async def on_raw_reaction_remove(self, payload: discord.raw_models.RawReactionActionEvent) -> None:
        res = await self.bot.bd.fetch({'message_id': payload.message_id}, mode='all', category='reactroles')
        for i in res.value:
            if i['reaction'] == payload.emoji.name and i['channel_id'] == payload.channel_id:
                role = discord.utils.get(self.bot.get_guild(payload.guild_id).roles, id=int(i['role_id']))
                try:
                    guild = self.bot.get_guild(payload.guild_id)
                    member = guild.get_member(payload.user_id)
                    await member.remove_roles(role, reason='Роли за реакцию.')
                except discord.errors.Forbidden:
                    return
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.member.VoiceState, after: discord.member.VoiceState) -> None:
        # <AuditLogEntry id=998929831263731784 action=AuditLogAction.member_disconnect user=<Member id=728165963480170567 name='MegaWatt_' discriminator='1114' bot=False nick=None guild=<Guild id=742394556405907457 name="Viola's house" shard_id=0 chunked=True member_count=13>>>
        again = False
        async def clearrooms(category: discord.CategoryChannel, acceptedvoicechannel: int):
            for x in category.voice_channels:
                if len(x.members) == 0:
                    if x.id != acceptedvoicechannel:
                        try:
                            await x.delete()
                        except discord.errors.NotFound:
                            pass
        res = await self.bot.bd.fetch({'guildid': member.guild.id}, category='rooms')
        if res.status:
            category: discord.CategoryChannel = discord.utils.get(member.guild.categories, id=int(res.value['catid']))
            self.bot.loop.create_task(clearrooms(category=category, acceptedvoicechannel=int(res.value['voiceid'])))
            if after.channel.id == int(res.value['voiceid']):
                if category is not None:
                    overwrites = {
                        member.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                        member: discord.PermissionOverwrite(manage_channels=True)
                    }
                    a = await category.create_voice_channel(name=f'Канал {member.name}', user_limit=2, overwrites=overwrites)
                    await member.move_to(a)
        if before.channel is None and after.channel is not None:
            print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {member.name} зашел в канал {after.channel.name} | {after.channel.guild.name}')
            self.buffer.append({'memberid': member.id, 'guildid': member.guild.id, 'amount': 0})
            res = await self.bot.bd.fetch({'guildid': after.channel.guild.id, 'memberid': member.id}, category='voice')
            if not res.status:
                if not member.bot:
                    await self.bot.bd.add({'guildid': after.channel.guild.id, 'memberid': member.id, 'amount': 0}, category='voice')
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
        elif before.channel is not None and after.channel is not None:
            if before.channel.name != after.channel.name:
                print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {member.name} перешёл в канал {after.channel.name} из {before.channel.name} | {before.channel.guild.name}')

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error) -> None:
        if isinstance(error, CommandNotFound):
            return
        elif isinstance(error, commands.ChannelNotFound):
            embed = ViolaEmbed(ctx=ctx, format='error')
            embed.description = '`Такой канал не найден.`'
            await ctx.message.reply(embed=embed)
        elif isinstance(error, commands.NotOwner):
            return
        elif isinstance(error, MissingPermissions):
            await ctx.channel.send(embed=discord.Embed(title='Ошибка', description=f'`Вам не хватает прав для данного действия.`\n`Вам нужны права:` **{error.missing_permissions[0]}**', color=discord.Color.red()))
        elif isinstance(error, MissingRequiredArgument):
            await ctx.send(f'`Не хватает аргументов. Укажите аргумент:` **{error.param}**')
        elif isinstance(error, MemberNotFound):
            embed = ViolaEmbed(ctx=ctx, format='error')
            embed.description = '`Такой участник не найден.`'
            await ctx.message.reply(embed=embed)
        elif isinstance(error, DisabledCommand):
            await ctx.message.reply(error)
        else:
            raise error
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
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
                await self.bot.bd.remove({'guildid': ctx.guild.id, 'memberid': message.author.id}, category='messages')
                await self.bot.bd.add({'guildid': message.guild.id, 'memberid': message.author.id, 'amount': msgs+1}, category='messages')
                res = await self.bot.bd.fetch({'guildid': message.guild.id, 'memberid': message.author.id}, category='messages')
                msgs = res.value['amount']
                level2 = self.bot.GetLevel(msgs)
                if level1 < level2:
                    res = await self.bot.bd.fetch({'guildid': ctx.guild.id}, category='system')
                    if res.status:
                        channel = self.bot.get_channel(int(res.value['channelid']))
                        try:
                            return await channel.send(f'{message.author.mention} поднял свой уровень до **{level2[0]}**!')
                        except Exception:
                            return await message.reply(f'{message.author.mention} поднял свой уровень до **{level2[0]}**!')
                    await message.reply(f'{message.author.mention} поднял свой уровень до **{level2[0]}**!')

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
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
                if b - a > 10:
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
    async def on_message_edit(self, before: discord.message.Message, after: discord.message.Message) -> None:
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
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(events(bot))