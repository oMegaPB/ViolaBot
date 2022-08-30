import traceback, os, io, lavalink
import discord, asyncio, aiohttp
import datetime, contextlib
from typing import Optional, Dict, Any, List, Union, AsyncIterator
from discord.ext import commands
from Config.utils import Paginator
from Config.assets.database import MongoDB
from Config.components import TicketButtons, TicketClose, RoomActions, ViolaEmbed
from PIL import Image, ImageFont, ImageDraw
cwd = os.path.join(os.getcwd(), 'Config')

class Viola(commands.Bot):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bd = MongoDB() # database connection
        self.session: aiohttp.ClientSession = None # filled in setup_hook
        self.lavalink: lavalink.Client = None
        print('-------------------------------------------')
        print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] [Viola/INFO]: Connected to database successfully.')
    
    async def sync(self) -> None:
        # guild = discord.Object(id=1000466637478178910)
        # self.tree.copy_global_to(guild=guild)
        await self.tree.sync() # guild=guild

    async def setup_hook(self) -> None:
        persistents = [TicketButtons(), TicketClose(), RoomActions()]
        for i in persistents:
            self.add_view(i)
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        for filename in os.listdir(os.path.join(cwd.replace('Config', ''), 'Cogs')):
            if filename.endswith(".py"):
                await self.load_extension(f"Cogs.{filename[:-3]}")
    
    async def get_log_channel(self, guildid: int) -> Optional[discord.TextChannel]:
        res = await self.bd.fetch({'guildid': guildid}, category='logs')
        if res.status:
            value = res.value
            return self.get_channel(int(value['channel_id']))
    
    async def get_voicestats_channel(self, guildid: int) -> Optional[discord.VoiceChannel]:
        res = await self.bd.fetch({'guildid': guildid}, category='voicemembers')
        if res.status:
            return self.get_channel(int(res.value['voiceid']))
    
    def format_time(self, seconds: Union[int, float]) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if seconds >= 3600:
            return f'{h:02d}:{m:02d}:{s:02d}'
        return f'{m:02d}:{s:02d}'
    
    async def prefix_check(self, interaction: discord.Interaction, answer: str):
        res = await self.bd.fetch({'guildid': interaction.guild.id}, category='prefixes')
        if res.status:
            return res.value['prefix'] == answer
        else:
            return 's!' == answer
    
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
    
    async def get_welcome_image(self, member: discord.Member, format: str = 'welcome') -> discord.File:
        if not member.avatar:
            avatar_url = 'https://raw.githubusercontent.com/AdvertiseYourServer/Default-Discord-Avatars/master/4.png'
        else:
            avatar_url = member.avatar.url
        im = Image.open(os.path.join(cwd, 'assets', 'image.png')).convert('RGBA')
        mainfont = ImageFont.truetype(os.path.join(cwd, 'assets', 'welcome_font.ttf'), size=25)
        async with self.session.get(avatar_url) as response:
            avatar = Image.open(io.BytesIO(await response.content.read())).resize((170, 170), 0).convert('RGBA')
            mask_im = Image.new("L", avatar.size, 0)
            draw = ImageDraw.Draw(mask_im)
            ellipse = Image.open(os.path.join(cwd, 'assets', 'rgb.png')).convert('RGBA').resize((210, 210))
            mask = Image.open(os.path.join(cwd, 'assets', 'rgbmask.png')).convert('L').resize((210, 210))
            text = ImageDraw.Draw(im)
            if format == 'welcome':
                text.text((220, 70), text='Добро пожаловать!', font=mainfont, fill=(255, 255, 255, 255))
            elif format == 'bye':
                text.text((220, 70), text='С тобой было приятно иметь дело!', font=mainfont, fill=(255, 255, 255, 255))
            else:
                raise ValueError('Invalid format')
            im.paste(ellipse, (2, 22), mask=mask)
            draw.ellipse((0, 0, 170, 170), fill=255)
            im.paste(avatar, (20, 42), mask=mask_im)
            draw.ellipse((0, 0, 100, 100), fill=255)
            self.imgforfont= im.crop((210, 0, 750, 250))
            def set_size(fontsize: int) -> Image.Image:
                tmp= self.imgforfont.copy()
                font = ImageFont.truetype(os.path.join(cwd, 'assets', 'welcome_font.ttf'), size=fontsize)
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
                    self.imgforfont = tmp
                    return
                else:
                    set_size(fontsize=fontsize-1)
            self.loop.run_in_executor(None, set_size, 50)
            im.paste(self.imgforfont, (210, 0))
            image_bytes = io.BytesIO()
            im.save(image_bytes, format='PNG')
            image_bytes.seek(0)
            return discord.File(image_bytes, filename=f'{format}User.png')
    
    async def voice_members(self, bots: bool = False) -> AsyncIterator[discord.Member]:
        for g in self.guilds:
            for c in g.voice_channels:
                for m in c.members:
                    if bots:
                        yield m
                    else:
                        if not m.bot:
                            yield m
    
    def format_level(self, amount: int) -> List[int]:
        levels = {0: 10, 1: 50, 2: 100, 3: 175, 4: 250, 5: 350, 6: 500, 7: 650, 8: 800, 9: 1000, 10: 1200}
        for level, need in levels.items():
            if amount >= need:
                continue
            return [level, need]
        amount -= 1000
        actual_level = 10
        while True:
            if amount - 200 >= 0:
                amount -= 200
                actual_level += 1
            else:
                return [actual_level, 1200 + (200 * (actual_level-10))]

class ViolaHelp(commands.HelpCommand):
    def __init__(self) -> None:
        super().__init__()
    
    async def send_bot_help(self, mapping: Dict[Any, Any]) -> None:
        async with self.context.channel.typing():
            embeds = []
            for i, j in enumerate(mapping.keys()):
                with contextlib.suppress(AttributeError):
                    if j.__cog_name__ == 'events':
                        continue
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
       
    async def send_command_help(self, command: commands.Command) -> None:
        embed = ViolaEmbed(ctx=self.context)
        embed.color = discord.Color.dark_gray()
        embed.title = f'Команда {command.name}'
        embed.description = command.description
        await self.context.send(embed=embed)
    
    async def command_not_found(self, command) -> None:
        return f'Команда {command} не найдена.'
