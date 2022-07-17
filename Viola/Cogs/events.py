import discord, requests, json, datetime, os, asyncio
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
        # print(f'{payload.member} Из {self.bot.get_guild(payload.guild_id).name} Поставил реакцию {payload.emoji.name} в канале {self.bot.get_channel(payload.channel_id).name}')
        pass
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.member.VoiceState, after: discord.member.VoiceState):
        if before.channel is None and after.channel is not None:
            print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {member.name} зашел в канал {after.channel.name} | {after.channel.guild.name}')
        elif before.channel is not None and after.channel is None:
            print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {member.name} покинул канал {before.channel.name} | {before.channel.guild.name}')
        elif before.channel is not None and after.channel is not None:
            if before.channel.name == after.channel.name:
                return
            print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {member.name} перешёл в канал {after.channel.name} из {before.channel.name} | {before.channel.guild.name}')

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, CommandNotFound):
            await ctx.send("`Неизвестная команда. Используйте s!help Для списка команд.`", delete_after = 25.0)
        elif isinstance(error, MissingPermissions):
            await ctx.send('`Вам не хватает прав.`', delete_after = 25.0)
        elif isinstance(error, MissingRequiredArgument):
            await ctx.send('`Не хватает аргументов.`', delete_after = 25.0)
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
            
async def setup(bot: commands.Bot):
    await bot.add_cog(events(bot))
