import discord, json, requests, os, threading, time, math, datetime
from discord.ext import commands
import traceback, random
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
from transliterate import translit
# apikey = os.environ.get('APIKEY')
apikey = 'de1102d9-c7fe-4c75-9844-e766adde9e94'
# -------------------------------------------------------------------------------------------
class stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command()
    async def amogus(self, ctx: commands.Context):
        embed = discord.Embed(description = 'ඞ', color = 0x33ff33)
        await ctx.send(embed = embed)

    @commands.command(aliases = ['s', ])
    async def stats(self, ctx: commands.Context, *username): # [rank, level_full, achi, karma, quests, friends, guild_all, tss, self.kd, names, links, self.uuid]
        res = requests.get(f'https://api.hypixel.net/key?key={apikey}').json()
        if str(res['success']) != 'True':
            await ctx.send('Проблемы с апи ключом. Скоро исправится.')
            return
        done = False
        if not username:
            try:
                with open(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__))).replace('Cogs', ''), 'Config', 'assets', 'linked.txt'), 'r') as file:
                    all = file.readlines()
                for i in all:
                    i = str(i).replace("'", '"').replace("\n", '')
                    i = json.loads(i)
                    if str(i['ctxid']) == str(ctx.author.id):
                        username = requests.get(f"https://api.mojang.com/user/profiles/{i['uuid']}/names").json()[-1]['name']
                        done = True
                        break
            except Exception:
                print(traceback.format_exc())
        if not done and not username:
            embed = discord.Embed(title = 'Error', description = 'Specify the username or link your account: s!link <username>', color = discord.Color.green())
            await ctx.send(embed = embed)
            return
        try:
            async with ctx.message.channel.typing():
                if isinstance(username, tuple):
                    profile = self.Stats(username[0])
                elif isinstance(username, str):
                    profile = self.Stats(username)
                try:
                    info = profile.GetStats(1)
                except Exception:
                    print(traceback.format_exc())
                embed = discord.Embed(title=info[12], url=f'https://plancke.io/hypixel/player/stats/{info[12]}', color = 0xfcf9ff)
                embed.set_author(name = f"Player Stats", icon_url=f'https://crafatar.com/avatars/{info[11]}?overlay=true')
                info[3] =  ('{:,}'.format(info[3]))
                part1 = f"Rank: {info[0]}\nLevel: {info[1][0]} ({info[1][1]})\nAchievement points: {info[2]}\nKarma: {info[3]}\nQuests Completed: {info[4]}\nFriends: {info[5]}"
                if str(info[6]) != '[]':
                    part2 = f"\n\nGuild: {info[6][0]}\nRole: {info[6][1]}\nLevel: {info[6][2]}\n\n"
                else:
                    part2 = f"\n\nGuild: -\n\n"
                if len(info[7]) == 3:
                    part3 = f"Last Login: <t:{info[7][0]}:R>\nFirst Login: <t:{info[7][1]}:R>\nCached Time: <t:{info[7][2]}:R>\n"
                elif len(info[7]) == 2:
                    part3 = f"Last Login: Hiden In Api\nFirst Login: <t:{info[7][0]}:R>\nCached Time: <t:{info[7][1]}:R>\n"
                else:
                    part3 = f"Last Login: undefined\nFirst Login: undefined\nCached Time: <t:{info[7][0]}:R>\n"
                part4 = f'\n| Game | K/D | W/L |\n| Bedwars | {info[8][0][0]} | {info[8][0][1]} |\n| Skywars | {info[8][1][0]} | {info[8][1][1]} |\n| Duels | {info[8][2][0]} | {info[8][2][1]} |\n| MM | {info[8][6][0]} | {info[8][6][1]} |\n\n'
                part5 = 'Names:\n'
                count = 0
                for i in range(len(info[9])):
                    try:
                        part5 += "`" + info[9][count] + "`" + ", " + "`" + str(info[9][count+1]) + "`" + '\n'
                        count += 2
                    except Exception:
                        try:
                            part5 += "`" + info[9][count] + "`" + '\n'
                            break
                        except Exception:
                            break
                part6 = '\nSocial Contacts:\n'
                try:
                    for key, value in info[10].items():
                        if key == 'YOUTUBE':
                            if not 'https://' in value:
                                part6 += f"{key}: [[**Click**]]({'https://' + value})\n"
                            else:
                                part6 += f"{key}: [[**Click**]]({value})\n"
                        elif key == 'TWITTER':
                            part6 += f"{key}: [[**Click**]]({value})\n"
                        elif key == 'TWITCH':
                            part6 += f"{key}: [[**Click**]]({value})\n"
                        elif key == 'HYPIXEL':
                            part6 += f"{key}: [[**Click**]]({value})\n"
                        elif key == 'INSTAGRAM':
                            part6 += f"{key}: [[**Click**]]({value})\n"
                        else:
                            part6 += f"{key}: {value}\n"
                except Exception:
                    part6 += '-\n'
                embed.description = part1 + part2 + part3 + part4 + part5 + part6
                bytes = BytesIO()
                info[13].save(bytes, format='PNG')
                bytes.seek(0)
                dfile = discord.File(bytes, filename=f'{info[12]}.png')
                embed.set_footer(text=f'uuid: {info[11]}')
                channel = self.bot.get_channel(930508587736915989)
                img = await channel.send(file = dfile)
                embed.set_image(url=img.attachments[0].url)
                await ctx.send(embed=embed)
        except Exception:
            embed = discord.Embed(title = 'Error', description = 'Could not find this player.', color = discord.Color.green())
            await ctx.send(embed=embed)
    # --------------------------------------------------------------------------------------------------
    class Stats:
        path = str(os.path.dirname(os.path.realpath(__file__))).replace('/Config', '')
        def __init__(self, username):
            self._response, self._friends, self._guild, self.kd, self.tss = None, None, None, [['-', '-', '-', '-', '-', '-'], ['-', '-', '-', '-', '-', '-'], ['-', '-', '-', '-', '-', '-'], ['-', '-', '-', '-', '-', '-'], ['-', '-', '-', '-', '-', '-'], ['-', '-', '-', '-', '-', '-'], ['-', '-', '-', '-', '-', '-']], []
            try:
                self.resp = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{username}?').json()
                self.username = self.resp['name']
                self.uuid = self.resp['id']
                self.SetInfo()
            except Exception:
                raise Exception('Could not find this player')
        def _getResponse(self):
            self._response = requests.get(f'https://api.hypixel.net/player?key={apikey}&uuid={self.uuid}').json()
        def _getFriends(self):
            self._friends = requests.get(f'https://api.hypixel.net/friends?key={apikey}&uuid={self.uuid}').json()
        def _getGuild(self):
            self._guild = requests.get(f'https://api.hypixel.net/guild?key={apikey}&player={self.uuid}').json()
        def SetInfo(self):
            threading.Thread(target=self._getResponse).start()
            threading.Thread(target=self._getFriends).start()
            threading.Thread(target=self._getGuild).start()
        def getGuildLevel(self, number):
            levels = [100000, 150000, 250000, 500000, 750000, 1000000, 1250000, 1500000, 2000000, 2500000]
            level = 0
            for i in levels:
                if number - i > 0:
                    number -= i
                    level += 1
                else: break
            level += 1
            for i in range(100000):
                if number - 3000000 > 0:
                    number -= 3000000
                    level += 1
                else: break
            return level
        def GetKDWL(self):
            while True:
                try:
                    len(self._response)
                    break
                except Exception: 
                    pass
            try:
                # ['Bedwars', 'Arcade', 'Arena', 'GingerBread', 'Paintball', 'Quake', 'VampireZ', 'Walls', 'UHC', 'HungerGames', 'TNTGames', 'Walls3', 'Battleground', 'SkyWars', 'MCGO', 'SuperSmash', 'TrueCombat', 'SpeedUHC', 'SkyBlock', 'Duels', 'Pit', 'MurderMystery', 'BuildBattle', 'Legacy', 'Housing', 'WoolGames']
                bwkills = int(self._response['player']['stats']['Bedwars']['kills_bedwars'])
                bwfinalkills = int(self._response['player']['stats']['Bedwars']['final_kills_bedwars'])
                bwdeaths = self._response['player']['stats']['Bedwars']['deaths_bedwars']
                bwwins = self._response['player']['stats']['Bedwars']['wins_bedwars']
                bwlosses = self._response['player']['stats']['Bedwars']['losses_bedwars']
                self.kd[0][0] = round(int(bwkills)/int(bwdeaths), 2)
                self.kd[0][1] = round(int(bwwins)/int(bwlosses), 2)
                self.kd[0][2] = bwkills + bwfinalkills
                self.kd[0][3] = bwdeaths
                self.kd[0][4] = bwwins
                self.kd[0][5] = bwlosses
            except Exception:
                pass
            try:
                swkills = self._response['player']['stats']['SkyWars']['kills']
                swdeaths = self._response['player']['stats']['SkyWars']['deaths']
                swwins = self._response['player']['stats']['SkyWars']['wins']
                swlosses = self._response['player']['stats']['SkyWars']['losses']
                self.kd[1][0] = round(int(swkills)/int(swdeaths), 2) 
                self.kd[1][1] = round(int(swwins)/int(swlosses), 2)
                self.kd[1][2] = swkills
                self.kd[1][3] = swdeaths
                self.kd[1][4] = swwins
                self.kd[1][5] = swlosses
            except Exception:
                pass
            try:
                dkills = self._response['player']['stats']['Duels']['kills']
                ddeaths = self._response['player']['stats']['Duels']['deaths']
                dwins = self._response['player']['stats']['Duels']['wins']
                dlosses = self._response['player']['stats']['Duels']['losses']
                self.kd[2][0] = round(int(dkills)/int(ddeaths), 2) 
                self.kd[2][1] = round(int(dwins)/int(dlosses), 2)
                self.kd[2][2] = dkills
                self.kd[2][3] = ddeaths
                self.kd[2][4] = dwins
                self.kd[2][5] = dlosses
            except Exception:
                pass
            try:
                mwkills = self._response['player']['stats']['Walls3']['kills']
                mwdeaths = self._response['player']['stats']['Walls3']['deaths']
                mwwins = self._response['player']['stats']['Walls3']['wins']
                mwlosses = self._response['player']['stats']['Walls3']['losses']
                self.kd[3][0] = round(int(mwkills)/int(mwdeaths), 2) 
                self.kd[3][1] = round(int(mwwins)/int(mwlosses), 2)
                self.kd[3][2] = mwkills
                self.kd[3][3] = mwdeaths
                self.kd[3][4] = mwwins
                self.kd[3][5] = mwlosses
            except Exception:
                pass
            try:
                uhckills = int(self._response['player']['stats']['UHC']['kills_solo']) + int(self._response['player']['stats']['UHC']['kills'])
                uhcdeaths = int(self._response['player']['stats']['UHC']['deaths_solo']) + int(self._response['player']['stats']['UHC']['deaths'])
                uhcwins = int(self._response['player']['stats']['UHC']['wins_solo']) + int(self._response['player']['stats']['UHC']['wins'])
                self.kd[4][0] = round(int(uhckills)/int(uhcdeaths), 2) 
                self.kd[4][2] = uhckills
                self.kd[4][3] = uhcdeaths
                self.kd[4][4] = uhcwins
            except Exception:
                pass
            try:
                bsgkills = self._response['player']['stats']['HungerGames']['kills']
                bsgdeaths = self._response['player']['stats']['HungerGames']['deaths']
                bsgwins = int(self._response['player']['stats']['HungerGames']['wins']) + int(self._response['player']['stats']['HungerGames']['wins_teams'])
                self.kd[5][0] = round(int(bsgkills)/int(bsgdeaths), 2) 
                self.kd[5][2] = bsgkills
                self.kd[5][3] = bsgdeaths
                self.kd[5][4] = bsgwins
            except Exception:
                pass
            try:
                mmkills = self._response['player']['stats']['MurderMystery']['kills']
                mmdeaths = self._response['player']['stats']['MurderMystery']['deaths']
                mmwins = self._response['player']['stats']['MurderMystery']['wins']
                self.kd[6][0] = round(int(mmkills)/int(mmdeaths), 2) 
                self.kd[6][1] = round(int(self._response['player']['stats']['MurderMystery']['games'])/int(mmwins), 2)
                self.kd[6][2] = mmkills
                self.kd[6][3] = mmdeaths
                self.kd[6][4] = mmwins
            except Exception:
                pass
            return self.kd
        def GetStats(self, *ifimage):
            self.GetKDWL()
            while True:
                try:
                    friends = len(self._friends['records'])
                    len(self._response)
                    len(self._guild)
                    try:
                        guild = self._guild['guild']['name']
                        for i in range(len(self._guild['guild']['members'])):
                            if self._guild['guild']['members'][i]['uuid'] == self.uuid:
                                guild_rank = self._guild['guild']['members'][i]['rank']
                                guild_rank = translit(guild_rank, language_code='ru', reversed=True)
                        guild_level = self.getGuildLevel(int(self._guild['guild']['exp']))
                        guild_all = [guild, guild_rank.capitalize(), guild_level]
                    except TypeError:
                        guild_all = []
                    break
                except Exception as e:
                    time.sleep(0.01)
            # Rank Information
            def GetRank(response):
                if self.username.lower() == 'technoblade':
                    return 'PIG+++'
                try:
                    try:
                        if self._response['player']['monthlyPackageRank'] == "SUPERSTAR":
                            return "MVP++"
                    except Exception:
                        pass
                    try:
                        if self._response['player']['packageRank'] == "MVP_PLUS":
                            return "MVP+"
                    except Exception:
                        pass
                    if self._response['player']['rank'] == "YOUTUBER":
                        return "YouTube"
                    elif self._response['player']['rank'] == "ADMIN":
                        return "Admin"
                except Exception:
                    pass
                try:
                    if self._response['player']['newPackageRank'] == 'VIP_PLUS':
                        return "VIP+"
                    elif self._response['player']['newPackageRank'] == 'MVP_PLUS':
                        return "MVP+"
                    elif self._response['player']['newPackageRank'] == 'VIP':
                        return "VIP"
                    elif self._response['player']['newPackageRank'] == 'MVP':
                        return "MVP"
                    else:
                        pass
                except Exception as e:
                    return 'Default'
                return 'Default'
            rank = GetRank(self._response)
            # Level Information
            try:
                level = round((math.sqrt((2 * self._response["player"]["networkExp"]) + 30625) / 50) - 2.5, 2)
                level_full = str(level).split('.')
                level_full[1] = str(level_full[1] + "%")
                if str(level_full[1])[0] == '0':
                    level_full[1] = str(level_full[1])[1] + "%"
            except Exception:
                level_full = [0, '0%']
            # Achievement Points Information
            try:
                achi = self._response['player']['achievementPoints']
            except Exception:
                achi = 0
            # Karma Information
            try:
                karma = self._response['player']['karma']
            except Exception:
                karma = 0
            # Quests Information
            try:
                quests = int(self._response['player']['achievements']['general_quest_master'])
                for i in range(2013, 2030):
                    try:
                        quests += self._response['player'][f'completed_christmas_quests_{i}']
                    except Exception:
                        pass
            except Exception:
                quests = 0
            # names
            names = []
            names_raw = requests.get(f'https://api.mojang.com/user/profiles/{self.uuid}/names').json()
            for i in names_raw:
                try:
                    names.append(i['name'])
                except Exception:
                    pass
            # lastlogin/firstlogin/current
            try:
                self.tss = [str(self._response['player']['lastLogin'])[:-3], str(self._response['player']['firstLogin'])[:-3], str(time.time()).split('.')[0]]
            except Exception:
                try:
                    self.tss = [str(self._response['player']['firstLogin'])[:-3], str(time.time()).split('.')[0]]
                except Exception:
                    self.tss = [str(time.time()).split('.')[0]]
            try:
                links = self._response['player']['socialMedia']['links']
            except Exception:
                links = []
            try:
                self.color = self._response['player']['rankPlusColor']
            except Exception:
                pass
            self._response = None
            self.info = [rank, level_full, achi, karma, quests, friends, guild_all, self.tss, self.kd, names, links, self.uuid, self.username]
            if not ifimage:
                return self.info
            else:
                self.FormImage()
                self.info2 = [rank, level_full, achi, karma, quests, friends, guild_all, self.tss, self.kd, names, links, self.uuid, self.username, self.img]
                return self.info2
        def FormImage(self):
            plusikVip = '#f9fa00'
            Vip = '#66ff00'
            img_color = '#242424'
            img = Image.new('RGB', (1200, 1550), color=img_color)
            font = ImageFont.truetype(os.path.join(os.path.dirname(os.path.realpath(__file__)).replace('Cogs', ''), 'Config', 'assets', 'shrift.ttf'), size=75)
            font2 = ImageFont.truetype(os.path.join(os.path.dirname(os.path.realpath(__file__)).replace('Cogs', ''), 'Config', 'assets', 'shrift.ttf'), size=60)
            font3 = ImageFont.truetype(os.path.join(os.path.dirname(os.path.realpath(__file__)).replace('Cogs', ''), 'Config', 'assets', 'shrift.ttf'), size=45)
            mainfont = ImageFont.truetype(os.path.join(os.path.dirname(os.path.realpath(__file__)).replace('Cogs', ''), 'Config', 'assets', 'main.ttf'), size=35)
            draw_text = ImageDraw.Draw(img)
            # =---------------------------------------------------------------------------------------------------------------------------
            colors = {'BLACK':'#000000', 'DARK_BLUE':'#1619ff', 'DARK_GREEN':'#026340', 'DARK_AQUA':'#0acdde', 'DARK_RED':'#ab1d0b', 'DARK_PURPLE':'#9400d3', 'GOLD':'#ffd700', 'GRAY':'#808080', 'DARK_GRAY':'#45433b', 'BLUE':'#1b98f7', 'GREEN':'#00e600', 'AQUA':'#008cf0', 'RED':'#ff0000', 'YELLOW':'#fffe06', 'WHITE':'#ffffff', 'LIGHT_PURPLE':'#9d81ba'}
            try:
                if not "§" in self._guild['guild']['tag']:
                    guild_tag = f"[{self._guild['guild']['tag'].encode('ascii', errors='ignore').decode('utf-8')}]"
                else:
                    guild_tag_l = list(self._guild['guild']['tag'])
                    pos = -1
                    for i in guild_tag_l:
                        pos += 1
                        if i == "§":
                            try:
                                guild_tag_l.pop(pos)
                                guild_tag_l.pop(pos)
                            except Exception:
                                pass
                    guild_tag = "[" + "".join(guild_tag_l) + "]"
                guild_color = colors[self._guild['guild']['tagColor']]
            except Exception:
                guild_tag = ''
                guild_color = img_color
            # ---------------------------------------------------------------------------
            nickname = Image.new('RGB', (860, 68), color=img_color)
            draw_nick = ImageDraw.Draw(nickname)
            # ---------------------------------------------------------------------------
            if self.info[0] == 'VIP+':
                draw_nick.text((10, -5), f'[{self.info[0][:-1]}  ] {self.info[12]}', font=font2 ,fill=Vip, anchor='la')
                draw_nick.text((135, -5), f'+', font=font2 ,fill=plusikVip, anchor='la')
                right = 0
                pixels = nickname.load()
                for i in range(nickname.size[0]):
                    for j in range(nickname.size[1]):
                        if pixels[i, j] == (252, 249, 255):
                            pass
                        else:
                            if pixels[i, j] == (102, 255, 0):
                                if i > right:
                                    right = i
                draw_nick.text((right + 15, -5), f'{guild_tag}', font=font2 ,fill=guild_color, anchor='la')
            elif self.info[0] == 'Default':
                draw_nick.text((10, -5), f'{self.info[12]}', font=font2 ,fill="#707070", anchor='la')
                right = 0
                pixels = nickname.load()
                for i in range(nickname.size[0]):
                    for j in range(nickname.size[1]):
                        if pixels[i, j] == (252, 249, 255):
                            pass
                        else:
                            if pixels[i, j] == (112, 112, 112):
                                if i > right:
                                    right = i
                draw_nick.text((right + 15, -5), f'{guild_tag}', font=font2 ,fill=guild_color, anchor='la')
            elif self.info[0] == 'VIP':
                draw_nick.text((10, -5), f'[{self.info[0]}] {self.info[12]}', font=font2 ,fill=Vip, anchor='la')
                right = 0
                pixels = nickname.load()
                for i in range(nickname.size[0]):
                    for j in range(nickname.size[1]):
                        if pixels[i, j] == (252, 249, 255):
                            pass
                        else:
                            if pixels[i, j] == (102, 255, 0):
                                if i > right:
                                    right = i
                draw_nick.text((right + 15, -5), f'{guild_tag}', font=font2 ,fill=guild_color, anchor='la')
            elif self.info[0] == 'MVP':
                draw_nick.text((10, -5), f'[{self.info[0]}] {self.info[12]}', font=font2 ,fill='#4db2ff', anchor='la')
                right = 0
                pixels = nickname.load()
                for i in range(nickname.size[0]):
                    for j in range(nickname.size[1]):
                        if pixels[i, j] == (252, 249, 255):
                            pass
                        else:
                            if pixels[i, j] == (77, 178, 255):
                                if i > right:
                                    right = i
                draw_nick.text((right + 15, -5), f'{guild_tag}', font=font2 ,fill=guild_color, anchor='la')
            elif self.info[0] == 'MVP+':
                draw_nick.text((10, -5), f'[{self.info[0][:-1]}  ] {self.info[12]}', font=font2 ,fill='#4db2ff', anchor='la')
                try:
                    draw_nick.text((172, -5), f'+', font=font2 ,fill=colors[self.color], anchor='la')
                except Exception:
                    draw_nick.text((172, -5), f'+', font=font2 ,fill=colors['GOLD'], anchor='la')
                right = 0
                pixels = nickname.load()
                for i in range(nickname.size[0]):
                    for j in range(nickname.size[1]):
                        if pixels[i, j] == (252, 249, 255):
                            pass
                        else:
                            if pixels[i, j] == (77, 178, 255):
                                if i > right:
                                    right = i
                draw_nick.text((right + 15, -5), f'{guild_tag}', font=font2 ,fill=guild_color, anchor='la')
            elif self.info[0] == 'MVP++':
                draw_nick.text((10, -5), f'[{self.info[0][:-2]}    ] {self.info[12]}', font=font2 ,fill=colors['GOLD'], anchor='la')
                try:
                    draw_nick.text((172, -5), f'++', font=font2 ,fill=colors[self.color], anchor='la')
                except Exception:
                    draw_nick.text((172, -5), f'++', font=font2 ,fill=colors['GOLD'], anchor='la')
                right = 0
                pixels = nickname.load()
                for i in range(nickname.size[0]):
                    for j in range(nickname.size[1]):
                        if pixels[i, j] == (252, 249, 255):
                            pass
                        else:
                            if pixels[i, j] == (255, 215, 0):
                                if i > right:
                                    right = i
                draw_nick.text((right + 15, -5), f'{guild_tag}', font=font2 ,fill=guild_color, anchor='la')
            elif self.info[0] == 'YouTube':
                draw_nick.text((10, -5), f'[{self.info[0]}] {self.info[12]}', font=font2 ,fill=colors['RED'], anchor='la')
                right = 0
                pixels = nickname.load()
                for i in range(nickname.size[0]):
                    for j in range(nickname.size[1]):
                        if pixels[i, j] == (252, 249, 255):
                            pass
                        else:
                            if pixels[i, j] == (255, 0, 0):
                                if i > right:
                                    right = i
                draw_nick.text((right + 15, -5), f'{guild_tag}', font=font2 ,fill=guild_color, anchor='la')
            elif self.info[0] == 'Admin':
                draw_nick.text((10, -5), f'[{self.info[0]}] {self.info[12]}', font=font2 ,fill=colors['RED'], anchor='la')
                right = 0
                pixels = nickname.load()
                for i in range(nickname.size[0]):
                    for j in range(nickname.size[1]):
                        if pixels[i, j] == (252, 249, 255):
                            pass
                        else:
                            if pixels[i, j] == (255, 0, 0):
                                if i > right:
                                    right = i
                draw_nick.text((right + 15, -5), f'{guild_tag}', font=font2 ,fill=guild_color, anchor='la')
            elif self.info[0] == 'PIG+++':
                draw_nick.text((10, -5), f'[{self.info[0][:-3]}      ] {self.info[12]}', font=font2 ,fill=colors['LIGHT_PURPLE'], anchor='la')
                draw_nick.text((140, -5), f'+++', font=font2 ,fill=colors['YELLOW'], anchor='la')
                right = 0
                pixels = nickname.load()
                for i in range(nickname.size[0]):
                    for j in range(nickname.size[1]):
                        if pixels[i, j] == (252, 249, 255):
                            pass
                        else:
                            if pixels[i, j] == (157, 129, 186):
                                if i > right:
                                    right = i
            # ------------------------------------------------------------------------------------------------------------------------------
            try:
                members = len(self._guild['guild']['members'])
            except:
                members = False
            if members:
                gexp = []
                int_gexp = []
                for i in range(members):
                    if self._guild['guild']['members'][i]['uuid'] == self.uuid:
                        a = self._guild['guild']['members'][i]['expHistory']
                        for j in a.values():
                            int_gexp.append(j)
                            j = ('{:,}'.format(j))
                            gexp.append(j)
            # ------------------------------------------------------------------------------------------------------------------------------
            draw_text.text((230, 50), f'Player Stats', font=font, fill='#ffffff', anchor='mm')
            draw_text.text((35, 176), f'Level:\n{self.info[1][0]} ({self.info[1][1]})', font=mainfont, fill='#ffffff', anchor='la')
            draw_text.text((370, 240), f'Achievement\npoints:\n{self.info[2]}', font=mainfont, fill='#ffffff', anchor='mm')
            try:
                total = 0
                for i in range(len(int_gexp)):
                    total += int_gexp[i]
                total = ('{:,}'.format(total))
                if len(list(self.info[6][0])) > 15:
                    self.info[6][0] = self.info[6][0].split(' ')
                    self.info[6][0] = "\n".join(self.info[6][0])
                draw_text.text((540, 180), f'Guild:\n{self.info[6][0]}\n\nRole: {self.info[6][1]}\nLevel: {self.info[6][2]}\nMembers: {members}\n\nGexp:\nToday: {gexp[0]}\nWeek: {total}', font=mainfont, fill='#ffffff')
            except Exception:
                draw_text.text((580, 225), f'Guild:\n-', font=mainfont, fill='#ffffff', anchor='mm')
            self.info[3] = ('{:,}'.format(self.info[3]))
            self.info[4] = ('{:,}'.format(self.info[4]))
            draw_text.text((35, 310), f'Karma:\n{self.info[3]}', font=mainfont, fill='#ffffff', anchor='la')
            draw_text.text((330, 355), f'Quests:\n{self.info[4]}', font=mainfont, fill='#ffffff', anchor='mm')
            draw_text.text((35, 430), f'Friends:\n{self.info[5]}', font=mainfont, fill='#ffffff', anchor='la')
            if len(self.info[7]) == 3:
                lastlogin = str(datetime.datetime.fromtimestamp(int(self.info[7][0])))
                firstlogin = str(datetime.datetime.fromtimestamp(int(self.info[7][1])))
            elif len(self.info[7]) == 2:
                firstlogin = str(datetime.datetime.fromtimestamp(int(self.info[7][1])))
                lastlogin = 'Hiden In Api'
            else:
                firstlogin = 'undefined'
                lastlogin = 'undefined'
            draw_text.text((35, 675), f'First Login:\n{firstlogin}', font=mainfont, fill='#ffffff', anchor='la')
            draw_text.text((540, 675), f'Last Login:\n{lastlogin}', font=mainfont, fill='#ffffff', anchor='la')
            kdl = self.info[8] # bw, sw, duels, mw, uhc(kd, kills, deaths, wins) // K/D, W/L, kills, deaths, wins, losses
            # ------------------------------------------------------------------------------------------------------------------------------
            draw_text.text((35, 790), f'Game:\n\nBedWars\n\nSkywars\n\nDuels\n\nMegaWalls\n\nUHC\n\nBSG\n\nMurder\nMystery', font=mainfont, fill='#ffffff', anchor='la')
            draw_text.text((270, 790), f'Wins\n\n{kdl[0][4]}\n\n{kdl[1][4]}\n\n{kdl[2][4]}\n\n{kdl[3][4]}\n\n{kdl[4][4]}\n\n{kdl[5][4]}\n\n\n{kdl[6][4]}', font=mainfont, fill='#ffffff', anchor='la')
            draw_text.text((540, 790), f'Kills\n\n{kdl[0][2]}\n\n{kdl[1][2]}\n\n{kdl[2][2]}\n\n{kdl[3][2]}\n\n{kdl[4][2]}\n\n{kdl[5][2]}\n\n\n{kdl[6][2]}', font=mainfont, fill='#ffffff', anchor='la')
            draw_text.text((700, 790), f'K/D\n\n{kdl[0][0]}\n\n{kdl[1][0]}\n\n{kdl[2][0]}\n\n{kdl[3][0]}\n\n{kdl[4][0]}\n\n{kdl[5][0]}\n\n\n{kdl[6][0]}', font=mainfont, fill='#ffffff', anchor='la')
            draw_text.text((860, 790), f'W/L\n\n{kdl[0][1]}\n\n{kdl[1][1]}\n\n{kdl[2][1]}\n\n{kdl[3][1]}\n\n{kdl[4][1]}\n\n{kdl[5][1]}\n\n\n{kdl[6][1]}', font=mainfont, fill='#ffffff', anchor='la')
            # ------------------------------------------------------------------------------------------------------------------------------
            draw_text.text((900, 55), str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M')) + " GMT+3", font=font3, fill='#ffffff', anchor='mm')
            response = requests.get(f'https://crafatar.com/renders/body/{self.uuid}?overlay=true')
            skin = Image.open(BytesIO(response.content))
            skin = skin.resize((213, 480), Image.NEAREST)
            pixels = skin.load()
            for i in range(skin.size[0]):
                for j in range(skin.size[1]):
                    if pixels[i, j] == (0, 0, 0, 0):
                        pixels[i, j] = (36, 36, 36, 0)
            img.paste(skin, (900, 150))
            img.paste(nickname, (10, 100))
            self.img = img
# -------------------------------------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(stats(bot))
