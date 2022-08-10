import requests, json, asyncio, time, base64, os
from typing import Union
from dataclasses import dataclass,field
from bs4 import BeautifulSoup
from urllib.parse import quote
from hashlib import sha1
from hmac import new as hmac_new
from io import BytesIO, TextIOWrapper

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

class YT:
    async def getYT(query: str) -> Union[YTVideo, bool]:
        """
        |coro|    
        
        Returns first video search result on youtube.
        
        """
        response = requests.get(f'https://www.youtube.com/results?search_query={quote(query)}').text
        a = BeautifulSoup(response, 'lxml')
        data = json.loads(str(a.findAll('script')[-6].text).replace('var ytInitialData = ', '').replace(';', ''))['contents']["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]
        try:
            try:
                dummy = data['playlistRenderer']
                return False
            except KeyError:
                ident = data["videoRenderer"]["videoId"]
        except KeyError:
            query = data['showingResultsForRenderer']['correctedQuery']['runs'][0]['text']
            data = await YT.getYT(query)
        try:
            thumb = data["videoRenderer"]["thumbnail"]["thumbnails"][0]["url"]
            title = data["videoRenderer"]["title"]["runs"][0]["text"]
            author = data["videoRenderer"]["longBylineText"]["runs"][0]["text"]
            url = "https://www.youtube.com" + data["videoRenderer"]["longBylineText"]["runs"][0]["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
            duration = data["videoRenderer"]["lengthText"]["simpleText"]
            views = str(repr(data["videoRenderer"]["viewCountText"]["simpleText"]).replace(' просмотров', '').replace('xa0', '').replace('\\', '').replace("'", '').replace(' просмотра', '').replace(' просмотр', '').replace(' views', ''))
            views = ('{:,}'.format(int(views)))
            return YTVideo(ident, thumb, title, author, url, duration, views)
        except TypeError:
            return data
class HerokuRecognizer:
    async def get_shazam_data(music_bytes: bytes) -> str:
        r = requests.post("https://nameless-sierra-10297.herokuapp.com/api/v1", files={"b_data": music_bytes})
        if r.status_code == 200:
            return r.text
        else:
            raise Exception(f"API status code {r.status_code}")
    async def recognize_API(music_bytes: bytes) -> Song:
        shazam_data = await HerokuRecognizer.get_shazam_data(music_bytes)
        song_data = json.loads(shazam_data)["data"]
        song = Song(song_data[1]["track"]["title"],
                    song_data[1]["track"]["subtitle"],
                    song_data[1]["track"]["share"].get("image"),
                    song_data[1]["track"]["url"])
        return song

class ACRcloud:
    def __init__(self):
        data = '7c19864d9fe6b40ad4c0b1d29985bc6e:QejhENR15m68DS35n8vYz91f3GpR8tjq5X68yL58'.split(':')
        # data = os.environ.get('ARCLOUD').split(':')
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
# loop = asyncio.get_event_loop()
# print(loop.run_until_complete(YT.getYT('imagine dragons')))