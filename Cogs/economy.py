import discord, datetime
from discord import app_commands
from discord.ext import commands
from contextlib import suppress
from Config.core import Viola

class economy(commands.Cog, description='**Экономика.**'):
    def __init__(self, bot: Viola):
        self.bot = bot
    
    @commands.command()
    async def work(self, ctx: commands.Context):
        now = datetime.datetime.now().timestamp()
        res = await self.bot.bd.fetch({'guildid': ctx.guild.id}, category='workers')
        if res.status:
            return await ctx.channel.send
# -----------------------------------------------------------------------------------------------------------
async def setup(bot: Viola):
    await bot.add_cog(economy(bot))