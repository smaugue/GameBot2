# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import discord
from Packs.Botloader import owner_permission, Data, Bot
import asyncio
from discord.ext import commands
from discord.ext.commands import Context

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        Owner.app_command.deleter

    @commands.command(name="off")
    async def off(self, ctx: Context):
        if not owner_permission.check(ctx.author.id):
            return
        await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game("Arrret en cour..."))
        await ctx.send("Bot was offline.")
        await asyncio.sleep(1)
        print("")
        Bot.console("INFO", f'Bot Closed')
        print("")
        await self.bot.close()
        
    @commands.command(name="invits")
    async def invits(self, ctx: Context):
        if not owner_permission.check(ctx.author.id):
            return
        for guild in self.bot.guilds:
            try:
                invite = await guild.text_channels[0].create_invite(max_uses=1, unique=True)
                await ctx.send(f'Invitation pour le serveur {guild.name}: {invite.url}')
            except discord.Forbidden:
                 print(f"Le bot n'a pas les permissions nécessaires pour créer une invitation dans le serveur {guild.name}")