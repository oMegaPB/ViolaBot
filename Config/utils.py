import requests, json, asyncio, time, base64, os, discord, aiohttp
from discord.ext import commands
from typing import List, Union
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
from urllib.parse import quote
from hashlib import sha1
from hmac import new as hmac_new

# Dataclasses ------------------------------------------------------------------------------
@dataclass
class YTVideo:
    identifier : str
    thumbnail_url: str
    title: str
    author: str
    author_url: str
    duration: str
    view_count: str
@dataclass
class Song:
    title: str
    author: str
    thumbnail_url: str = field(default=None)
    shazam_url: str = field(default=None)
# Functions -----------------------------------------------------------------------------------
async def yt_search(query: str) -> Union[YTVideo, bool]:
    """
    |coro|    
    
    Returns first video search result on youtube.
    
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://www.youtube.com/results?search_query={quote(query)}') as response:
            data = await response.text()
    a = BeautifulSoup(data, 'lxml')
    data = json.loads(str(a.findAll('script')[-6].text).replace('var ytInitialData = ', '').replace(';', ''))['contents']["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]
    try:
        try:
            data['playlistRenderer']
            return False
        except KeyError:
            ident = data["videoRenderer"]["videoId"]
    except KeyError:
        query = data['showingResultsForRenderer']['correctedQuery']['runs'][0]['text']
        data = await yt_search(query)
    try:
        thumb = data["videoRenderer"]["thumbnail"]["thumbnails"][0]["url"]
        title = data["videoRenderer"]["title"]["runs"][0]["text"]
        author = data["videoRenderer"]["longBylineText"]["runs"][0]["text"]
        url = "https://www.youtube.com" + data["videoRenderer"]["longBylineText"]["runs"][0]["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
        duration = data["videoRenderer"]["lengthText"]["simpleText"]
        views = str(repr(data["videoRenderer"]["viewCountText"]["simpleText"]).replace(' просмотров', '').replace('xa0', '').replace('\\', '').replace("'", '').replace(' просмотра', '').replace(' просмотр', '').replace(' views', ''))
        try:
            views = ('{:,}'.format(int(views)))
        except Exception:
            views = views
        return YTVideo(ident, thumb, title, author, url, duration, views)
    except TypeError:
        return data
# Classes -----------------------------------------------------------------------------------
class HerokuRecognizer:
    async def get_shazam_data(self, music_bytes: bytes) -> str:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post("https://nameless-sierra-10297.herokuapp.com/api/v1", data={"b_data": music_bytes}) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    raise aiohttp.ClientConnectionError(f"API status code {response.status}\nПопробуйте еще раз.")    
    async def recognize_API(self, music_bytes: bytes) -> Song:
        shazam_data = await self.get_shazam_data(music_bytes)
        try:
            song_data = json.loads(shazam_data)["data"]
            song = Song(song_data[1]["track"]["title"],
                        song_data[1]["track"]["subtitle"],
                        song_data[1]["track"]["share"].get("image"),
                        song_data[1]["track"]["url"])
            return song
        except KeyError:
            return False
class ACRcloud:
    def __init__(self):
        data = os.environ.get('ARCLOUD').split(':')
        self.key = data[0]
        self.secret = data[1].encode()
    async def recognize(self, audio_bytes: bytes) -> Union[Song, bool]:
        timestamp = str(time.time())
        audio_bytes = base64.b64encode(audio_bytes)
        string_to_sign = ("%s\n%s\n%s\n%s\n%s\n%s" % ("POST","/v1/identify", self.key, "audio", "1", timestamp)).encode()
        sign = base64.b64encode(hmac_new(bytes(self.secret), bytes(string_to_sign), sha1).digest())
        data = {
            "access_key": self.key,
            "sample_bytes": 2 ** 20,
            "sample": audio_bytes,
            "timestamp": timestamp,
            "signature": sign,
            "data_type": "audio",
            "signature_version": "1",
            "timeout": 10
        }
        result = requests.post(f'http://identify-eu-west-1.acrcloud.com/v1/identify', data).json()
        if result["status"]['msg'] == 'Success':
            try:
                title = result['metadata']['music'][0]['title'].encode('l1').decode('utf-8')
            except KeyError:
                title = 'undefined'
            try:
                author = result['metadata']['music'][0]["artists"][0]['name'].encode('l1').decode('utf-8')
            except KeyError:
                author = 'undefined'
            try:
                thumbnail = f"https://i.ytimg.com/vi/{result['metadata']['music'][0]['external_metadata']['youtube']['vid']}/hqdefault.jpg"
            except KeyError:
                thumbnail = 'https://i.ytimg.com/vi/undefined/hqdefault.jpg'
            shazam = 'https://www.shazam.com/ru'
            return Song(title, author, thumbnail, shazam)
        return False
class Paginator(discord.ui.View):
    def __init__(self, *, timeout=60.0, embeds: List[discord.Embed], ctx: commands.Context, bot: commands.Bot):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.count = 0
        self.ctx = ctx
        self.bot = bot
        if len(self.embeds) < 2:
            raise ValueError('You must have at least 2 embeds here.')
        for i, embed in enumerate(self.embeds):
            try:
                embed.set_footer(text=f'{ctx.guild.name} Страница {i+1}/{len(embeds)}', icon_url=f'{ctx.guild.icon.url}')
            except Exception:
                embed.set_footer(text=f'{ctx.guild.name} Страница {i+1}/{len(embeds)}', icon_url=f'{self.bot.user.avatar.url}')
    @discord.ui.button(label="⏮️", style=discord.ButtonStyle.gray, disabled=True)
    async def prevall(self, interaction:discord.Interaction, button: discord.ui.Button):
        self.count = 0
        button.disabled = True
        x: discord.ui.Button
        for x in self.children:
            if x.label == '⏪':
                if not x.disabled:
                    x.disabled = True
            elif x.label == '⏩' or x.label == '⏭️':
                if x.disabled:
                    x.disabled = False
        await interaction.message.edit(embed=self.embeds[self.count], view=self)
        await interaction.response.defer()
    @discord.ui.button(label="⏪", style=discord.ButtonStyle.gray, disabled=True)
    async def previous(self, interaction:discord.Interaction, button: discord.ui.Button):
        self.count -= 1
        if self.count == 0:
            button.disabled = True
            for x in self.children:
                if x.label == '⏮️':
                    if not x.disabled:
                        x.disabled = True
        x: discord.ui.Button
        for x in self.children:
            if x.label == '⏩' or x.label == '⏭️':
                if x.disabled:
                    x.disabled = False
        await interaction.message.edit(embed=self.embeds[self.count], view=self)
        await interaction.response.defer()
    @discord.ui.button(label="⏩", style=discord.ButtonStyle.gray)
    async def next(self, interaction:discord.Interaction, button: discord.ui.Button):
        self.count += 1
        if self.count + 1 == len(self.embeds):
            button.disabled = True
            for x in self.children:
                if x.label == '⏭️':
                    if not x.disabled:
                        x.disabled = True
        x: discord.ui.Button
        for x in self.children:
            if x.label == '⏪' or x.label == '⏮️':
                if x.disabled:
                    x.disabled = False
        await interaction.message.edit(embed=self.embeds[self.count], view=self)
        await interaction.response.defer()
    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.gray)
    async def nextall(self, interaction:discord.Interaction, button: discord.ui.Button):
        self.count = len(self.embeds) - 1
        button.disabled = True
        x: discord.ui.Button
        for x in self.children:
            if x.label == '⏩':
                if not x.disabled:
                    x.disabled = True
            elif x.label == '⏪' or x.label == '⏮️':
                if x.disabled:
                    x.disabled = False
        await interaction.message.edit(embed=self.embeds[self.count], view=self)
        await interaction.response.defer()
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(embed=discord.Embed(title='Ошибка.', description=f'<@!{interaction.user.id}>\nВы не можете взаимодействовать с этим сообщением, т.к его вызвал другой человек.', color=discord.Color.red()), ephemeral=True)
            return False
        return True
    @discord.ui.button(label="❌", style=discord.ButtonStyle.red)
    async def close(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
            