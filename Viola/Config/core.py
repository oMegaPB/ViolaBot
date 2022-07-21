import discord
from discord.ext import commands

class Viola(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)