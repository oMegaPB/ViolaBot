import discord, lavalink
import datetime, typing
from discord.ext import commands
from datetime import datetime as dt, timedelta
from Config.assets.newdb import MongoDB

class Viola(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bd = MongoDB()
        self.time = kwargs.get('start_time')
        print('-------------------------------------------')
        print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] [Viola/INFO]: Connected to database successfully.')
        self.lavalinkmode = 'public'
        print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] [Viola/INFO]: selected lavalink mode: [{self.lavalinkmode}].')

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
    
    def GetTime(self, seconds: int) -> str:
        sec = timedelta(seconds=seconds)
        d = dt(1,1,1) + sec
        if int(d.second) < 10:
            second = '0' + str(d.second)
        else: second = d.second
        if int(d.minute) < 10:
            minute = '0' + str(d.minute)
        else: minute = d.minute
        if int(d.hour) < 10:
            hour = '0' + str(d.hour)
        else: hour = d.hour
        if int(d.day-1) < 10:
            day = '0' + str(d.day - 1)
        else: day = d.day
        if d.day-1 != 0:
            res = "{}:{}:{}:{}".format(day-1, hour, minute, second).replace('00', '0')
        else:
            if d.hour != 0:
                res = "{}:{}:{}".format(hour, minute, second).replace('00', '0')
            else:
                res = "{}:{}".format(minute, second).replace('00', '0')
        if res[-2:] == ':0':
            res += "0"
        return res
    
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
        super().__init__(**kwargs)

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

