# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import discord
from discord.ext import commands
from discord import Colour
from Packs.embeder import EmbedGenerator

class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="test_pagined_embed")
    async def commande_embed(self, ctx):
        title = "Test de Pagination d'Embed"
        color = 0x3498db
        content = {f"Champ {i+1}": f"Contenu du champ {i+1}" for i in range(100)}

        generator = EmbedGenerator()
        await generator.send_paginated_embed(ctx, title=title, color=Colour(color), content=content)

    @commands.command(name="test_pagined_embed_d")
    async def commande_embed_d(self, ctx, number: int):
        title = "Test de Pagination d'Embed"
        color = 0x3498db

        content = {f"Champ {i+1}": f"Contenu du champ {i+1}" for i in range(number)}

        generator = EmbedGenerator()
        await generator.send_paginated_embed(ctx, title=title, color=Colour(color), content=content)


async def setup(bot):
    await bot.add_cog(Test(bot))