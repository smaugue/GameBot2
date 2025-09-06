# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

#discord
import discord
from discord.ext import commands
from discord.ext.commands import Context
#autre
import os
import asyncio
import argparse
from datetime import datetime
#self.Packs
from Packs.automod import AutoMod
from Packs.interpretor import parse_actions
from Packs.version import Version, BOT_VERSION, BOT_VERSION_DATE
from Packs.Botloader import tz, owner_permission, Data, Bot

def main():
    parser = argparse.ArgumentParser(description='Scripte Bot V1.2')
    parser.add_argument('Botname', type=str, default="Bot", help='Nom du bot à lancer')
    parser.add_argument('--pasword', type=str, default="", help="Mot de passe")
    args = parser.parse_args()
    Bot(args.Botname, str(args.pasword))

if __name__ == '__main__':
    main()

r = "n"
u = ""

class BotClient(commands.Bot):
    __slots__ = ()  # réduit la consommation mémoire

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game("Chargement des cookis!")
        )
        Bot.console("INFO", f'Logged in V{BOT_VERSION} ({BOT_VERSION_DATE})')

        # Chargement des cogs depuis ./Cogs
        for filename in os.listdir("./Cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"Cogs.{filename[:-3]}")
                    Bot.console("INFO", f"Cog {filename} chargé.")
                except Exception as e:
                    Bot.console("WARN", f"Erreur lors du chargement du cog {filename}: {e}")

        Bot.console("INFO", f'Logged in as {self.user} (ID: {self.user.id})')

        try:
            synced = await self.tree.sync()
            Bot.console("INFO", f'Synced {len(synced)} slash commands')
        except Exception as e:
            Bot.console("ERROR", f'Error syncing slash commands: {e}')

        Bot.console("INFO", "Bot is ready.")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name="coocke you!")
        )


    async def restart(self, ctx: Context, update):
        if owner_permission.check(ctx.author.id) != True:
            return await ctx.reply("Vous ne disposez pas des autorisations nécéssaire.")
        if update == "--update":
            global u
            u = update
        await self.change_presence(status=discord.Status.dnd, activity=discord.Game("Redémarage en cour..."))
        await ctx.send("Bot was offline for restart.")
        await asyncio.sleep(1)
        print("")
        Bot.console("INFO", f'Bot Closed for restart')
        print("")
        global r
        r = "y"
        await self.close()

    async def versions(self, ctx: Context):
        patch = None
        date, patch = Version.get_patch()
        check = Version.check()
        # Cache de la langue pour éviter des appels répétés en mémoire
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))

        if check == "j":
            description, color, url = language("version_j_description"), discord.Colour.green(), "https://cdn3.emoji.gg/emojis/2990_yes.png"
        elif check == "o":
            description, color, url = language("version_o_description"), discord.Colour.from_rgb(250, 0, 0), "https://cdn3.emoji.gg/emojis/1465-x.png"
        else:
            description, color, url = language("version_b_description"), discord.Colour.orange(), "https://cdn3.emoji.gg/emojis/3235_warning2.png"
        embed = discord.Embed(title=language("version_maj_note"), description=description, color=color)
        embed.set_thumbnail(url=url)
        embed.add_field(name=language("version_bot"), value=BOT_VERSION, inline=False)
        embed.add_field(name=language("version_laster"), value=Version.LASTER_VERSION, inline=False)
        if patch:
            embed.add_field(name=language("version_patch_note", date=date), value=patch, inline=False)
        return await ctx.reply(embed=embed)

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        guild_language = Bot.get_language(Data.get_guild_conf(message.guild.id, Data.GUILD_LANGUAGE))
        blw, blws = {}, {}
        if message.content:
            if Data.get_guild_conf(message.guild.id, Data.AUTOMOD_ENABLE) == "1":
                level = Data.get_guild_conf(message.guild.id, Data.AUTOMOD_LEVEL)
                if not level: 
                    level = 3
                blw, blws = AutoMod.check_message(message.content, level=level)
                v = AutoMod.automod_version()
        if len(blw) != 0:
            automod_channel_id = Data.get_guild_conf(message.guild.id, Data.AUTOMOD_CHANNEL)
            if automod_channel_id is not None:
                channel = message.guild.get_channel(int(automod_channel_id))
                if channel:
                    # Détection de la zone (DM ou canal classique)
                    if isinstance(message.channel, discord.channel.DMChannel):
                        zone = guild_language("spam_dm_report_title")
                    else:
                        zone = guild_language("spam_dm_report_blocked_title")
                    startTime = datetime.strftime(datetime.now(tz), '%H:%M:%S')
                    embed = discord.Embed(title=zone, description=startTime, color=discord.Color.brand_red())
                    embed.set_thumbnail(url=message.author.avatar.url)
                    embed.add_field(name=guild_language("spam_dm_embed_user"), value=message.author.mention, inline=False)
                    embed.add_field(name=guild_language("spam_dm_embed_target"), value=message.jump_url, inline=False)
                    embed.add_field(name=guild_language("spam_dm_embed_message"), value=message.content, inline=False)
                    embed.add_field(name=guild_language("spam_dm_embed_status"), value=guild_language("spam_dm_status_pending"), inline=False)
                    embed.set_footer(text=guild_language("api_autmod_version").format(v=v))

                    # Préparer le bouton pour l'action de modération
                    view = discord.ui.View()
                    item = discord.ui.Button(style=discord.ButtonStyle.danger, label=guild_language("moderate_button"), custom_id="automod_action", disabled=False)
                    view.add_item(item=item)
                    # Ajouter les mots détectés
                    for key in blw:
                        embed.add_field(name=guild_language("spam_dm_embed_detected_word").format(word=key),
                                        value=guild_language("spam_dm_embed_similarity").format(similarity=round(blws[key], 2) * 100, detected=blw[key]),
                                        inline=False)
                    # Ajouter les pièces jointes si présentes
                    if message.attachments:
                        for attachment in message.attachments:
                            embed.add_field(name=guild_language("spam_dm_embed_attachment"), value=attachment.proxy_url, inline=False)

                    # Envoyer le message dans le canal d'auto-modération
                    await channel.send(embed=embed, view=view)
        data = Data.get_guild_conf(message.guild.id, Data.CUSTOM_COMMANDS_NAMES)
        if data:
            if len(data) > 0:
                data = data.split("\n")
            ctx = await bot.get_context(message)
            message_content = message.content.strip()
            space_index = message_content.find(' ')
            command = message_content if space_index == -1 else message_content[:space_index]
            if command in data:
                executor = Data.get_guild_conf(message.guild.id, command)
                try:
                    action_list = parse_actions(ctx, executor)
                    for action in action_list:
                        await action.execute(ctx)
                except Exception as e:
                    await ctx.send(guild_language("error_cusstom_commande").format(error=str(e)))
                    Bot.console("ERROR", e)
        await self.process_commands(message)

# Pour limiter la consommation mémoire, nous utilisons uniquement les intents requis
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = client = BotClient(command_prefix=Bot.Prefix, intents=intents, description="Belouga.exe is watching you!!!")
bot.remove_command('help')

@bot.command(name="restart")
async def restart(ctx, *, update=None):
    await bot.restart(ctx, update)

@bot.hybrid_command(name="version", help="Version and update patch notes.")
async def version(ctx):
    await bot.versions(ctx=ctx)

try:
    bot.run(Bot.Token)
except:
    print("Bad Pasword")
os.system(f"python Launcher.py --bot {Bot.Name} --restart {r} --pasword {Bot.Pasword} {u}")
