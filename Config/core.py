import discord, lavalink, asyncio, aiohttp
import datetime, typing
from discord.ext import commands
from Config.utils import embedButtons
from Config.assets.database import MongoDB

class Viola(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bd = MongoDB()
        print('-------------------------------------------')
        print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] [Viola/INFO]: Connected to database successfully.')
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
    
    async def sync(self) -> None:
        # guild = discord.Object(id=1000466637478178910)
        # self.tree.copy_global_to(guild=guild)
        await self.tree.sync() # guild=guild
    
    async def getLogChannel(self, guildid) -> typing.Optional[discord.TextChannel]:
        res = await self.bd.fetch({'guildid': guildid}, category='logs')
        if res.status:
            value = res.value
            channel: discord.TextChannel = self.get_channel(int(value['channel_id']))
            return channel
        return None  
    
    def GetTime(self, seconds: int):
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if seconds >= 3600:
            return f'{h:02d}:{m:02d}:{s:02d}'
        return f'{m:02d}:{s:02d}'
    
    def GetLevel(self, amount: int) -> int:
        amount += 1
        level = 0
        additional = 1
        if amount < 10:
            return [0, 10]
        else:
            amount -= 10
            level += 1
            if amount - 40 > 0:
                amount -= 40
                level += 1
                if amount - 50 > 0:
                    amount -= 50
                    level += 1
                    for i in range(2):
                        if amount - 75 > 0:
                            amount -= 75
                            level += 1
                        else: 
                            break
                    if amount - 100 > 0:
                        amount -= 100
                        level += 1
                        for i in range(3):
                            if amount - 150 > 0:
                                amount -= 150
                                level += 1
                            else: 
                                break
                        if amount - 200 > 0:
                            amount -= 200
                            level += 1
                        while True:
                            if amount - 200 > 0:
                                amount -= 200
                                level += 1
                                additional += 1
                            else:
                                break
        levels = {'0': 10, '1': 50 , '2': 100, '3': 175, '4': 250, '5': 350, '6': 500, '7': 650, '8': 800, '9': 1000, '10': 1200}
        if str(level) in levels.keys():
            next = levels[f'{level}']
        else:
            additional = 200 * additional
            next = 1000 + additional
        return [level, next]

class ViolaEmbed(discord.Embed):
    def __init__(self, **kwargs):
        self.format = kwargs.pop('format') if 'format' in kwargs else 'success'
        self.ctx = kwargs.pop('ctx') if 'ctx' in kwargs else None
        if not isinstance(self.ctx, commands.Context) and self.ctx is not None:
            raise discord.errors.ClientException('ctx not context')
        super().__init__(**kwargs)
        if self.ctx:
            try:
                self.set_footer(text=f'{self.ctx.guild.name}', icon_url=f'{self.ctx.guild.icon.url}')
            except Exception:
                self.set_footer(text=f'{self.ctx.guild.name}', icon_url=f'{self.ctx.me.avatar.url}')
            try:
                self.set_thumbnail(url=f'{self.ctx.guild.icon.url}')
            except Exception:
                self.set_thumbnail(url=f'https://i.ytimg.com/vi/onTNE293NR0/hqdefault.jpg')
        colors = {'success': discord.Color.green(), 'warning': discord.Color.yellow(), 'error': discord.Color.red()}
        titles = {'success': 'Успешно.', 'warning': 'Внимание.', 'error': 'Ошибка.'}
        urls = {
            'success': 'https://cdn.discordapp.com/emojis/1006317088253681734.webp',
            'warning': 'https://cdn.discordapp.com/emojis/1006317089683951718.webp',
            'error': 'https://cdn.discordapp.com/emojis/1006317086471094302.webp'
        }
        self.set_author(icon_url=urls[self.format], name=titles[self.format])
        self.color = colors[self.format]

class CommandDisabled(commands.CommandError):
    """
    Exception that being raised while user running disabled command
    
    """
    pass

class ViolaHelp(commands.HelpCommand):
    def __init__(self):
        super().__init__()
    
    async def send_bot_help(self, mapping: dict):
        embeds = []
        for i, j in enumerate(mapping.keys()):
            try:
                if j.__cog_name__ == 'events':
                    continue
            except AttributeError:
                pass
            j: commands.Cog
            x: commands.Command
            embed = ViolaEmbed(ctx=self.context)
            title = j.__cog_name__ if j is not None else 'Команды администрации.'
            title += '\n' + j.__cog_description__ if j is not None else ''
            embed.title = title
            description = ''
            for x in mapping[j]:
                description += f'**{x.name}**\n'
            embed.description = description
            embeds.append(embed)
        await self.context.channel.send(embed=embeds[0], view=embedButtons(embeds=embeds, ctx=self.context, bot=self.context.bot))
       
    async def send_command_help(self, command: commands.Command):
        embed = ViolaEmbed(ctx=self.context)
        embed.title = f'Команда {command.name}'
        embed.description = command.description
        await self.context.send(embed=embed)
      
    async def send_group_help(self, group):
        await self.context.send("This is help group")
    
    async def send_cog_help(self, cog):
        await self.context.send("This is help cog")
    
    async def command_not_found(self, command):
        return f'Команда {command} не найдена.'

class LavalinkVoiceClient(discord.VoiceClient):
    def __init__(self, client: Viola, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        self.lavalink: lavalink.Client = self.client.lavalink
    async def on_voice_server_update(self, data):
        lavalink_data = {'t': 'VOICE_SERVER_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)
    async def on_voice_state_update(self, data):
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
