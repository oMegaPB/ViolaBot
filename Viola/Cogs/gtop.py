import discord
from discord.ext import commands
from discord.ext.commands.errors import MissingRequiredArgument
from Config.Gtop import Gtop
import traceback, random
from io import BytesIO

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
            guild = Gtop(name)
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

async def setup(bot):
    await bot.add_cog(gtop(bot))