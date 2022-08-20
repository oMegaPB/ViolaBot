import traceback, os, io
import discord, lavalink, asyncio, aiohttp
import datetime
from typing import Optional, Dict, Any, List, Union
from discord.ext import commands
from Config.utils import Paginator
from Config.assets.database import MongoDB
from PIL import Image, ImageFont, ImageDraw

class Viola(commands.Bot):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bd = MongoDB()
        print('-------------------------------------------')
        print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] [Viola/INFO]: Connected to database successfully.')
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
    
    async def sync(self) -> None:
        # guild = discord.Object(id=1000466637478178910)
        # self.tree.copy_global_to(guild=guild)
        await self.tree.sync() # guild=guild
    
    async def getLogChannel(self, guildid) -> Optional[discord.TextChannel]:
        res = await self.bd.fetch({'guildid': guildid}, category='logs')
        if res.status:
            value = res.value
            channel: discord.TextChannel = self.get_channel(int(value['channel_id']))
            return channel
    
    def format_time(self, seconds: Union[int, float]) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if seconds >= 3600:
            return f'{h:02d}:{m:02d}:{s:02d}'
        return f'{m:02d}:{s:02d}'
    
    async def get_marry_info(self, member: discord.Member) -> Optional[Dict[str, Any]]:
        res = await self.bd.fetch({'guildid': member.guild.id, 'memberid': member.id}, category='marry')
        if not res.status:
            res = await self.bd.fetch({'guildid': member.guild.id, 'partnerid': member.id}, category='marry')
            if res.status:
                args = {'main': member.id, 'partner': res.value['memberid'], 'date': res.value['date']}
                return args
        else:
            args = {'main': member.id, 'partner': res.value['partnerid'], 'date': res.value['date']}
            return args
    
    async def get_welcome_image(self, member: discord.Member) -> discord.File:
        if not member.avatar:
            avatar_url = 'https://raw.githubusercontent.com/AdvertiseYourServer/Default-Discord-Avatars/master/4.png'
        else:
            avatar_url = member.avatar.url
        im = Image.open(os.path.join(os.path.dirname(os.path.realpath(__file__)).replace('Cogs', ''), 'Config', 'assets', 'image.png')).convert('RGBA')
        mainfont = ImageFont.truetype(os.path.join(os.path.dirname(os.path.realpath(__file__)).replace('Cogs', ''), 'Config', 'assets', 'DejaVuSans.ttf'), size=25)
        async with self.session.get(avatar_url) as response:
            avatar = Image.open(io.BytesIO(await response.content.read())).resize((170, 170), 0).convert('RGBA')
            mask_im = Image.new("L", avatar.size, 0)
            draw = ImageDraw.Draw(mask_im)
            text = ImageDraw.Draw(im)
            text.text((220, 70), text='Добро пожаловать!', font=mainfont, fill=(255, 255, 255, 255))
            text.ellipse((10, 35, 200, 220), fill='#fcf3ff')
            draw.ellipse((0, 0, 170, 170), fill=255)
            im.paste(avatar, (20, 42), mask=mask_im)
            draw.ellipse((0, 0, 100, 100), fill=255)
            class globals:
                imgforfont= im.crop((210, 0, 750, 250))
            def set_size(fontsize: int) -> Image.Image:
                tmp=globals.imgforfont.copy()
                font = ImageFont.truetype(os.path.join(os.path.dirname(os.path.realpath(__file__)).replace('Cogs', ''), 'Config', 'assets', 'DejaVuSans.ttf'), size=fontsize)
                imdraw = ImageDraw.Draw(tmp)
                imdraw.text(text=f'{member.display_name}#{member.discriminator}', xy=(8, 115), font=font)
                pixels = tmp.load()
                breaked = False
                for i in range(475, 530):
                    for j in range(100, 150):
                        if pixels[i, j] == (255, 255, 255, 255):
                            breaked = True
                            break
                        if breaked:
                            break
                if not breaked:
                    globals.imgforfont = tmp
                    return
                else:
                    set_size(fontsize=fontsize-1)
            set_size(50)
            im.paste(globals.imgforfont, (210, 0))
            image_bytes = io.BytesIO()
            im.save(image_bytes, format='PNG')
            image_bytes.seek(0)
            return discord.File(image_bytes, filename=f'WelcomeScreen.png')
    
    def GetLevel(self, amount: int) -> List[int]:
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
                self.set_footer(text=f'{self.ctx.guild.name}', icon_url=f'{self.ctx.bot.user.avatar.url}')
            try:
                self.set_thumbnail(url=f'{self.ctx.guild.icon.url}')
            except Exception:
                self.set_thumbnail(url=self.ctx.bot.user.avatar.url)
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
    
    async def send_bot_help(self, mapping: Dict[Any, Any]):
        async with self.context.channel.typing():
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
                embed.color = discord.Color.dark_gray()
                title = j.__cog_name__ if j is not None else 'Без категории.'
                title += '\n' + j.__cog_description__ if j is not None else ''
                embed.title = title
                description = ''
                for x in mapping[j]:
                    aliases = ("`Псевдонимы: " + x.aliases[0] + "`") if len(x.aliases) > 0 else False
                    description += f'**{x.name}** {aliases if aliases else ""}\n'
                embed.description = description
                embeds.append(embed)
            await self.context.channel.send(embed=embeds[0], view=Paginator(embeds=embeds, ctx=self.context, bot=self.context.bot))
       
    async def send_command_help(self, command: commands.Command):
        embed = ViolaEmbed(ctx=self.context)
        embed.color = discord.Color.dark_gray()
        embed.title = f'Команда {command.name}'
        embed.description = command.description
        await self.context.send(embed=embed)
    
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
