import discord
from discord.ext import commands
from Config.assets.database import MongoDB

class Viola(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bd = MongoDB()

    async def sync(self):
        await self.tree.sync()