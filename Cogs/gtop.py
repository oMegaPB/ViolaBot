import discord, requests, threading, os
from discord.ext import commands
from discord.ext.commands.errors import MissingRequiredArgument
import traceback, random
from io import BytesIO
# apikey = os.environ.get('APIKEY')
apikey = 'de1102d9-c7fe-4c75-9844-e766adde9e94'

class gtop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = ['gtop', ])
    async def guild_top(self, ctx, *info):
        if not info:
            embed = discord.Embed(title='Guild top', description="Example: `s!gtop ML`, OR `s!gtop 3 DjagaArmy`", color=discord.Color.green())
            await ctx.send(embed=embed)
            return
        info = list(info)
        if len(info) == 1:
            day = 1
            name = info[0]
        elif len(info) == 2:
            day = info[0]
            info.pop(0)
            name = info[0]
        elif len(info) > 2:
            day = info[0]
            info.pop(0)
            name = " ".join(info)
        if int(day) > 7 or int(day) < 1:
            embed = discord.Embed(title='Error', description="Provide valid numbers between 1-7", color=discord.Color.green())
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title='One moment...', description="Collecting guild information...", color=discord.Color.green())
        message = await ctx.send(embed=embed)
        try:
            guild = self.Gtop(name)
            gexp = guild.GetGexp(int(day))
            try:
                total = gexp[-1]
            except Exception:
                pass
            if gexp != None:
                if gexp != 'None':
                    info = f'{gexp[1]}\n\n{gexp[2]}\n\n'
                    count = 0
                    for i in gexp[0]:
                        count += 1
                        name = i['name']
                        gexp = int(i['gexp'])
                        gexp =  ('{:,}'.format(gexp))
                        info += f'{count}. {name}: {gexp}\n'
                    info += f'\nmembers: {total}'
                    embed = discord.Embed(title='Guild GEXP Leaderboard', description="`" + info + "`", color=discord.Color.green())
                else:
                    embed = discord.Embed(title=f'{name}', description="Dead guild GG.", color=discord.Color.green())
            else:
                embed = discord.Embed(title='Error', description="Guild not found.", color=discord.Color.green())
            await message.edit(embed=embed)
        except Exception as e:
            print(traceback.format_exc())
            embed = discord.Embed(title='Error', description=f"`{e}`", color=discord.Color.red())
            await message.edit(embed=embed)
    class Gtop:
        def __init__(self, name):
            self.name = name
            self.all = ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-']
        def GetNamesThread(self, uuid, pos):
            self.all[pos] = (requests.get(f'https://api.mojang.com/user/profiles/{uuid}/names').json()[-1]['name'])
        def GetGexp(self, day):
            self.response = requests.get(f'https://api.hypixel.net/guild?key={apikey}&name={self.name}').json()
            if str(self.response['guild']) != 'None':
                top10 = []
                for i in range(len(self.response['guild']['members'])):
                    uuid = self.response['guild']['members'][i]['uuid']
                    gexp = list(self.response['guild']['members'][i]['expHistory'].values())[day-1]
                    if int(gexp) != 0:
                        top10.append({'uuid': uuid, 'gexp': int(gexp)})
                if len(top10) == 0:
                    return 'None'
                top10 = sorted(top10, key = lambda d: d['gexp'])
                count = -1
                topers = []
                if len(top10) < 10:
                    mems = len(top10)
                else:
                    mems = 10
                for i in range(mems):
                    topers.append(top10[count])
                    count -= 1
                final = []
                pos = 0
                for i in topers:
                    uuid = i['uuid']
                    threading.Thread(target=self.GetNamesThread, args=(uuid, pos)).start()
                    pos += 1
                while (10 - int(self.all.count("-"))) != len(topers):
                    pass
                count = 0
                for i in range(len(topers)):
                    final.append({'name': self.all[i], 'gexp': topers[count]['gexp']})
                    count +=1
                return [final, self.response['guild']['name'], list(self.response['guild']['members'][0]['expHistory'].keys())[day-1], len(self.response['guild']['members'])]

async def setup(bot):
    await bot.add_cog(gtop(bot))