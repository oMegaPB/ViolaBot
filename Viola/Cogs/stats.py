import discord, json, requests, os
from discord.ext import commands
from discord.ext.commands.errors import MissingRequiredArgument
from Config.Stats import Stats
import traceback, random
from io import BytesIO
class stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def amogus(self, ctx: commands.Context):
        embed = discord.Embed(description = 'ඞ', color = 0x33ff33)
        await ctx.send(embed = embed)

    @commands.command(aliases = ['s', ])
    async def stats(self, ctx: commands.Context, *username): # [rank, level_full, achi, karma, quests, friends, guild_all, tss, self.kd, names, links, self.uuid]
        done = False
        if not username:
            try:
                with open(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__))).replace('\\Cogs', ''), 'Config', 'assets', 'linked.txt'), 'r') as file:
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
            embed = discord.Embed(title = 'Wait...', description = 'Collecting Information...', color = discord.Color.green())
            message = await ctx.send(embed = embed)
            if isinstance(username, tuple):
                profile = Stats(username[0])
            elif isinstance(username, str):
                profile = Stats(username)
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
            else:
                part3 = f"Last Login: Hiden In Api\nFirst Login: <t:{info[7][0]}:R>\nCached Time: <t:{info[7][1]}:R>\n"
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
                        part6 += f"{key}: [Click]({value})\n"
                    elif key == 'TWITTER':
                        part6 += f"{key}: [Click]({value})\n"
                    elif key == 'TWITCH':
                        part6 += f"{key}: [Click]({value})\n"
                    elif key == 'HYPIXEL':
                        part6 += f"{key}: [Click]({value})\n"
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
            await message.edit(embed=embed)
        except Exception:
            embed = discord.Embed(title = 'Error', description = 'Could not find this player.', color = discord.Color.green())
            await message.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(stats(bot))
