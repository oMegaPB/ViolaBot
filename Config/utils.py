import requests, json, asyncio
from typing import Union
from dataclasses import dataclass,field
from bs4 import BeautifulSoup
from urllib.parse import quote

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
            views = str(repr(data["videoRenderer"]["viewCountText"]["simpleText"]).replace(' просмотров', '').replace('xa0', '').replace('\\', '').replace("'", '').replace(' просмотра', '').replace(' просмотр', ''))
            views = ('{:,}'.format(int(views)))
            return YTVideo(ident, thumb, title, author, url, duration, views)
        except TypeError:
            return data
class Recognizer:
    async def get_shazam_data(music_bytes: bytes) -> str:
        r = requests.post("https://nameless-sierra-10297.herokuapp.com/api/v1", files={"b_data": music_bytes})
        if r.status_code == 200:
            return r.text
        else:
            raise Exception(f"API status code {r.status_code}")
    async def recognize_API(music_bytes: bytes) -> Song:
        shazam_data = await Recognizer.get_shazam_data(music_bytes)
        song_data = json.loads(shazam_data)["data"]
        song = Song(song_data[1]["track"]["title"],
                    song_data[1]["track"]["subtitle"],
                    song_data[1]["track"]["share"].get("image"),
                    song_data[1]["track"]["url"])
        return song