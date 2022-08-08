import discord, requests, json, datetime, os
from discord.ext import commands
from discord.ext.commands.errors import CommandNotFound
# apikey = os.environ.get('APIKEY')
apikey = 'de1102d9-c7fe-4c75-9844-e766adde9e94'

def getDiscord(username):
    try:
        try:
            response = requests.get(f"https://api.hypixel.net/player?key={apikey}&uuid={requests.get(f'https://api.mojang.com/users/profiles/minecraft/{username}').json()['id']}").json()
        except requests.exceptions.JSONDecodeError:
            return 404
        return response['player']['socialMedia']['links']['DISCORD']
    except KeyError:
        return False
class link(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases = ['link', ])
    async def link_account(self, ctx: commands.Context, name):
        dis = getDiscord(name)
        if dis == 404:
            embed = discord.Embed(title = 'Error', description = f"`Player {name} Not Found.`", color = discord.Color.green())
            await ctx.send(embed = embed)
            return
        if str(dis) == str(ctx.author):
            with open(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__))).replace('Cogs', ''), 'Config', 'assets', 'linked.txt'), 'r') as file:
                all = file.readlines()
            uuid = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{name}').json()['id']
            ctxid = ctx.author.id
            for i in all:
                i = str(i).replace("'", '"').replace("\n", '')
                try:
                    i = json.loads(i)
                except Exception:
                    await ctx.send('`Successfully linked your account.`')
                    with open(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__))).replace('Cogs', ''), 'Config', 'assets', 'linked.txt'), 'a') as file:
                        file.write(str({"ctxid": ctxid, "uuid": uuid}) + "\n")
                        return
                if i['ctxid'] == ctxid:
                    name = requests.get(f"https://api.mojang.com/user/profiles/{i['uuid']}/names").json()[-1]['name']
                    await ctx.send(f'`Your account already linked with {name}`')
                    return
                elif i['uuid'] == uuid:
                    name = requests.get(f"https://api.mojang.com/user/profiles/{i['uuid']}/names").json()[-1]['name']
                    await ctx.send(f'`Account {name} already linked. linked id: {i["ctxid"]}`')
                    return
            await ctx.send('`Successfully linked your account.`')
            with open(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__))).replace('Cogs', ''), 'Config', 'assets', 'linked.txt'), 'a') as file:
                file.write(str({"ctxid": ctxid, "uuid": uuid}) + "\n")
        else:
            if dis:
                embed = discord.Embed(title = 'Error', description = f"`{name}'s discord does not match to your's`", color = discord.Color.green())
                await ctx.send(embed = embed)
            else:
                embed = discord.Embed(title = 'Error', description = f"`{name} does not have a discord specified.`", color = discord.Color.green())
                await ctx.send(embed = embed)

    @commands.command(aliases = ['unlink', ])
    async def unlink_account(self, ctx: commands.Context):
        with open(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__))).replace('Cogs', ''), 'Config', 'assets', 'linked.txt'), 'r') as file:
            all = file.readlines()
        count = 0
        for i in all:
            i = str(i).replace("'", '"').replace("\n", '')
            i = json.loads(i)
            if str(i['ctxid']) == str(ctx.author.id):
                all.pop(count)
                await ctx.send('`Successfully unlinked your account.`')
                break
            count += 1
        with open(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__))).replace('Cogs', ''), 'Config', 'assets', 'linked.txt'), 'w') as file:
            for j in all:
                file.write(j)
async def setup(bot: commands.Bot):
    await bot.add_cog(link(bot))