# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import discord
import Packs.Botloader
import asyncio
import os
from discord.ext import commands
from discord.ext.commands import Context
from gtts import gTTS
from random import randint

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot