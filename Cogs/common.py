# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import discord
import asyncio
import os
import time
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from random import randint
from typing import List
from Packs.automod import AutoMod
from Packs.Botloader import Data, Bot, Utilitary
from Packs.version import BOT_VERSION


class Common(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    async def cmd_autocompletion(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        cmds = ['join', 'leave', 'stop', 'vtts', 'ftts', 'dm', 'execute']
        return [
            app_commands.Choice(name=cmd, value=cmd)
            for cmd in cmds if current.lower() in cmd.lower()
        ]
    
    async def lg_autocompletion(self, interaction: discord.Interaction,current: str) -> List[app_commands.Choice[str]]:
            lgs = ['fr','ja','de','en']
            return [
                    app_commands.Choice(name=lg, value=lg)
                    for lg in lgs if current.lower() in lg.lower()
                ]

    @commands.hybrid_command(name="bugreport", help = f"Signaler un bug.")
    @app_commands.autocomplete(command = cmd_autocompletion)
    async def bugreport(self, ctx: Context, command, bug: str):
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        print(Bot.BotGuild)
        guild = self.bot.get_guild(int(Bot.BotGuild))
        print(guild)
        channel = guild.get_channel_or_thread(int(Bot.BugReportChannel))
        embed = discord.Embed(title=language("bugreport_title"), description=language("bugreport_description").format(cmd=command), colour=discord.colour.Color.orange())
        embed.add_field(name="Bug:", value=f"```{bug}```", inline=False)
        embed.add_field(name=language("bugreport_correction_state"), value=language("bugreport_correction_state_wainting"), inline=False)
        embed.set_footer(text=language("bot_version_markdown").format(v=BOT_VERSION))
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar)
        view = discord.ui.View()
        item = discord.ui.Button(style=discord.ButtonStyle.green, label=language("bugreport_corecte_button"), custom_id="bugreport_correction", disabled=False)
        view.add_item(item=item)
        item = discord.ui.Button(style=discord.ButtonStyle.grey, label=language("bugreport_not_receivable_button"), custom_id="bugreport_correction_n", disabled=False)
        view.add_item(item=item)
        await channel.send(embed=embed, view=view)
        await ctx.reply(language("bugreport_thanks"), ephemeral=True)
        
    @commands.hybrid_command(name="sayic", help = f"Permet de fair parler le bot dans un channel définit.")
    @commands.guild_only()
    async def sayInChannel(self, ctx: Context, channel : discord.TextChannel, text):
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        blw, blws = AutoMod.check_message(text)
        if len(blw) != 0:
            return await ctx.reply(language("bad_language_warning"))
        if Data.get_user_conf(ctx.guild.id, ctx.author.id, Data.SAYIC) != "1":
            return await Bot.on_refus_interaction(ctx)
        await channel.send(text)
        await ctx.reply(language("send_to_channel_success").format(channel=channel))

    @commands.hybrid_command(name="say", help = f"Permet de fair parler le bot.")
    @commands.guild_only()
    async def say(self, ctx: Context, text):
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        blw, blws = AutoMod.check_message(text)
        if len(blw) != 0:
            return await ctx.reply(language("bad_language_warning"))
        if Data.get_user_conf(ctx.guild.id, ctx.author.id, Data.SAY) == "0":
            return await Bot.on_refus_interaction(ctx)
        await ctx.send(text)

    # common.py
    @commands.hybrid_command(name="vtts")
    @app_commands.autocomplete(lg=lg_autocompletion)
    @commands.guild_only()
    async def vtts(self, ctx: Context, lg, *, text_to_speak: str):
        if lg == "ar":
            return await ctx.reply("Terrorist language not supported.", ephemeral=True)
    
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        blw, _ = AutoMod.check_message(text_to_speak)
        if blw:
            return await ctx.reply(language("bad_language_warning"))
        if Data.get_user_conf(ctx.guild.id, ctx.author.id, Data.VTTS) == "0":
            return await Bot.on_refus_interaction(ctx)
        if ctx.voice_client is None:
            return await ctx.send(language("voice_not_connected"), ephemeral=True)
    
        await ctx.defer()
        try:
            file_path = await Utilitary.maketts(text_to_speak, language=lg)
            await Utilitary.play_audio(ctx, file_path)
            await ctx.reply("Succès.", ephemeral=True)
        except Exception as e:
            await ctx.reply(f"Error: {e}")
    
    
    @commands.hybrid_command(name="ftts")
    @app_commands.autocomplete(lg=lg_autocompletion)
    @commands.guild_only()
    async def ftts(self, ctx: Context, lg, text_to_speak: str):
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        blw, _ = AutoMod.check_message(text_to_speak)
        if blw:
            return await ctx.reply(language("bad_language_warning"))
        if Data.get_user_conf(ctx.guild.id, ctx.author.id, Data.FTTS) == "0":
            return await Bot.on_refus_interaction(ctx)
    
        try:
            file_path = await Utilitary.maketts(text_to_speak, language=lg)
            async with ctx.typing():
                await ctx.send(file=discord.File(file_path))
        except Exception:
            return await ctx.reply(language("unpossible_naration"))
        finally:
            if os.path.exists(file_path):
                await asyncio.to_thread(os.remove, file_path)

        
    @commands.hybrid_command(name = "rdm")
    @commands.guild_only()
    async def randome(self, ctx: Context, min: int, max: int):
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        if Data.get_user_conf(ctx.guild.id, ctx.author.id, Data.RANDOM) == "0":
            return await Bot.on_refus_interaction(ctx)
        try:
            if int(max) > int(min):
                num = randint(int(min), int(max))
            else:
                num = randint(int(max), int(min))
            embed = discord.Embed(title="Random", description=language("random_commande_results").format(min=min, max=max))
            embed.set_thumbnail(url="https://media.tenor.com/IfbgWLbg_88AAAAC/dice.gif")
            embed.add_field(name=language("random_commande_results_number"), value=num, inline=False)
            await ctx.reply(embed=embed)
        except Exception as e:
            Bot.console("ERROR", e)

    @commands.hybrid_command(name="uptime")
    async def uptime(self, ctx: commands.Context):
        await ctx.defer()
        current_time = time.time()
        uptime_seconds = int(current_time - self.start_time)
        uptime_str = self.format_uptime(uptime_seconds)
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(title="Bot Status", color=discord.Color.blue())
        embed.add_field(name="Ping (Bot <-> Serveur)", value=f"{latency} ms", inline=False)
        embed.add_field(name="Uptime", value=uptime_str, inline=False)
        embed.add_field(name="Version", value=BOT_VERSION, inline=False)
        api_statut, api_version = AutoMod.handcheck()
        if api_statut:
            embed.add_field(name="AutoMod API Statut", value=f":green_circle: Online v{api_version}", inline=False)
        else:
            embed.add_field(name="AutoMod API Statut", value=f":red_circle: Offline", inline=False)
        await ctx.reply(embed=embed)

    def format_uptime(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        
        return f"{days}d {hours}h {minutes}m {seconds}s"
    

async def setup(bot):
    await bot.add_cog(Common(bot))