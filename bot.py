# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

#discord
from fileinput import filename
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
from Packs.version import Version, BOT_VERSION
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
    __slots__ = ()  # Utilisation de __slots__ pour réduire la consommation de mémoire

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        await self.change_presence(status=discord.Status.online, activity=discord.Game("Chargement des cookis!"))

        # Chargement des cogs
        for filename in os.listdir("./Cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"Cogs.{filename[:-3]}")  # Utilise self, pas bot
                    Bot.console("INFO", f"Cog {filename} chargé.")
                except Exception as e:
                    Bot.console("WARN", f"Erreur lors du chargement du cog {filename}: {e}")

        Bot.console("INFO", f'Logged in as {self.user} (ID: {self.user.id})')
        await self.versions(type="on_ready", ctx=None)

        # Synchronisation des commandes slash
        try:
            synced = await self.tree.sync()
            Bot.console("INFO", f'Synced {len(synced)} slash commands')
        except Exception as e:
            Bot.console("ERROR", f'Error syncing slash commands: {e}')

        # Changement de présence après tout chargement
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="coocke you!"))


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

    async def versions(self, type, ctx: Context):
        patch = None
        date, patch = Version.get_patch()
        if type == "on_ready":
            return Bot.console("INFO", f'Logged in V{BOT_VERSION} ({date})')

        check = Version.check()
        # Cache de la langue pour éviter des appels répétés en mémoire
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))

        if check == "j":
            description, color, url = language("version_j_description"), discord.Colour.green(), "https://cdn3.emoji.gg/emojis/2990_yes.png"
        elif check == "o":
            description, color, url = language("version_o_description"), discord.Colour.from_rgb(250, 0, 0), "https://cdn3.emoji.gg/emojis/1465-x.png"
        else:
            description, color, url = language("version_b_description"), discord.Colour.orange(), "https://cdn3.emoji.gg/emojis/3235_warning2.png"
        if type == "commande":
            embed = discord.Embed(title=language("version_maj_note"), description=description, color=color)
            embed.set_thumbnail(url=url)
            embed.add_field(name=language("version_bot"), value=BOT_VERSION, inline=False)
            embed.add_field(name=language("version_laster"), value=Version.LASTER_VERSION, inline=False)
            if patch:
                embed.add_field(name=language("version_patch_note", date=date), value=patch, inline=False)
            return await ctx.reply(embed=embed)

    async def on_interaction(self, interaction: discord.Interaction):
        # Pré-calcul de la langue en fonction du contexte (guild ou autre)
        if interaction.data["custom_id"] == "spam_dm":
            b, guild, user, msg = interaction.data["values"][0].split("/|/")
            guild_language = Bot.get_language(Data.get_guild_conf(int(guild), Data.GUILD_LANGUAGE))
        else:
            guild_language = Bot.get_language(Data.get_guild_conf(interaction.guild.id, Data.GUILD_LANGUAGE))
        if interaction.type == discord.InteractionType.application_command:
            await interaction.response.defer()  # Appel de la coroutine
        if interaction.type == discord.InteractionType.component:
            await interaction.response.defer()

            if interaction.data["custom_id"] == "spam_dm":
                if b == "y":
                    blackliste = Data.get_user_conf(guild, interaction.user.id, Data.DM_BLACKLISTE)
                    data = blackliste or ""
                    data += f"\n{user}"
                    Data.set_user_conf(guild, interaction.user.id, Data.DM_BLACKLISTE, data)
                    title = guild_language("spam_dm_report_blocked_title_oni")
                    placeholder = guild_language("spam_dm_report_blocked_placeholde_onir")
                else:
                    title = guild_language("spam_dm_report_title")
                    placeholder = guild_language("spam_dm_report_placeholder")

                automod_channel_id = Data.get_guild_conf(guild, Data.AUTOMOD_CHANNEL)
                try:
                    channel = bot.get_guild(int(guild)).get_channel(int(automod_channel_id))
                except Exception as e:
                    error_message = guild_language("error_admin_contact", guild=guild, error=e)
                    return await interaction.channel.send(error_message)

                start_time = datetime.strftime(datetime.now(tz), '%H:%M:%S')
                embed = discord.Embed(
                    title=guild_language("spam_dm_embed_title"),
                    description=start_time,
                    color=discord.Color.brand_red()
                )
                embed.add_field(name=guild_language("spam_dm_embed_user"), value=bot.get_user(int(user)).mention, inline=False)
                embed.add_field(name=guild_language("spam_dm_embed_target"), value=interaction.user.mention, inline=False)
                embed.add_field(name=guild_language("spam_dm_embed_message"), value=msg, inline=False)
                embed.add_field(name=guild_language("spam_dm_embed_status"), value=guild_language("spam_dm_status_pending"), inline=False)
                embed.add_field(name=guild_language("spam_dm_embed_measure"), value=placeholder, inline=False)

                view = discord.ui.View()
                item = discord.ui.Button(style=discord.ButtonStyle.danger, label=guild_language("moderate_button"), custom_id="automod_action", disabled=False)
                view.add_item(item=item)
                await channel.send(embed=embed, view=view)

                view = discord.ui.View()
                item = discord.ui.Select(
                    custom_id='spam_dm',
                    placeholder=placeholder,
                    options=[
                        discord.SelectOption(label="empty", value=f"empty"),
                    ],
                    disabled=True
                )
                view.add_item(item=item)
                await interaction.message.edit(view=view)

                embed = discord.Embed(
                    title=guild_language("spam_dm_user_embed_title"),
                    description=title,
                    color=discord.Colour.red()
                )
                return await interaction.channel.send(embed=embed)
            
            if interaction.data["custom_id"] == "bugreport_correction" and interaction.user.id == owner_permission.owner_id:
                view = discord.ui.View()
                item = discord.ui.Button(
                    style=discord.ButtonStyle.gray,
                    label=guild_language("bugreport_corrected_button"),
                    custom_id="bugreport_correction",
                    disabled=True
                )
                view.add_item(item=item)
                embeds = interaction.message.embeds  # Pas de copie inutile
                embed = embeds[0]
                embed.set_field_at(
                    index=1,
                    name=embed.fields[1].name,
                    value=guild_language("correction_done"),
                    inline=embed.fields[1].inline
                )
                embed.color = discord.Color.green()
                return await interaction.message.edit(embed=embed, view=view)

            if interaction.data["custom_id"] == "bugreport_correction_n" and interaction.user.id == owner_permission.owner_id:
                view = discord.ui.View()
                item = discord.ui.Button(
                    style=discord.ButtonStyle.gray,
                    label=guild_language("bugreport_not_receivable_button"),
                    custom_id="bugreport_correction_n",
                    disabled=True
                )
                view.add_item(item=item)
                embeds = interaction.message.embeds
                embed = embeds[0]
                embed.set_field_at(
                    index=1,
                    name=embed.fields[1].name,
                    value=guild_language("bugreport_correction_not_receivable"),
                    inline=embed.fields[1].inline
                )
                embed.color = discord.Color.dark_gray()
                return await interaction.message.edit(embed=embed, view=view)

            if interaction.data["custom_id"] == "automod_action":
                view = discord.ui.View()
                item = discord.ui.Button(
                    style=discord.ButtonStyle.success,
                    label=guild_language("moderated_button"),
                    custom_id="automod_action",
                    disabled=True
                )
                view.add_item(item=item)
                embeds = interaction.message.embeds
                embed = embeds[0]
                embed.set_field_at(
                    index=3,
                    name=embed.fields[3].name,
                    value=guild_language("moderated_by", user=interaction.user.mention),
                    inline=embed.fields[1].inline
                )
                embed.color = discord.Color.dark_red()
                return await interaction.message.edit(embed=embed, view=view)

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
    await bot.versions(type="commande", ctx=ctx)

@bot.event
async def on_error(event_method, *args, **kwargs):
    error = kwargs.get('error')
    if not error:
        return
    guild = bot.get_guild(Bot.BotGuild)
    channel = guild.get_channel_or_thread(Bot.BugReportChannel)
    embed = discord.Embed(title="Rapport de Bug Global", description=f"Une erreur est survenue au niveau de: `{event_method}`.", colour=discord.Colour.orange())
    embed.add_field(name="Bug:", value=f"```{error}```", inline=False)
    embed.add_field(name="Etat de correction:", value="En cour...", inline=False)
    embed.set_footer(text=f"Bot V{BOT_VERSION}")
    embed.set_author(name="Rapport Automatique", icon_url=bot.user.avatar.url)
    view = discord.ui.View()
    item = discord.ui.Button(style=discord.ButtonStyle.green, label="Corriger", custom_id="bugreport_correction")
    view.add_item(item=item)
    item = discord.ui.Button(style=discord.ButtonStyle.grey, label="Non Recevable", custom_id="bugreport_correction_n")
    view.add_item(item=item)
    await channel.send(embed=embed, view=view)

#@bot.event
async def on_command_error(ctx: Context, error):
    Bot.console("ERROR", error)
    language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
    command = ctx.command.qualified_name if ctx.command else "Unknown command"
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.reply(language("error_missing_argument"), ephemeral=True)
    if isinstance(error, commands.CommandNotFound):
        return await ctx.reply(language("error_command_no_found"), ephemeral=True)
    if isinstance(error, commands.MissingPermissions):
        return await ctx.reply(language("error_missing_permission"), ephemeral=True)
    if isinstance(error, discord.Forbidden):
        return await ctx.reply(language("error_missing_bot_permission"), ephemeral=True)
    if isinstance(error, discord.NotFound):
        return await ctx.reply('Discord possède une API de piètre qualité.')
    guild = bot.get_guild(Bot.BotGuild)
    channel = guild.get_channel_or_thread(Bot.BugReportChannel)
    embed = discord.Embed(title="Rapport de Bug", description=f"Commande concernée `{command}`.", colour=discord.Colour.orange())
    embed.add_field(name="Bug:", value=f"```{error}```", inline=False)
    embed.add_field(name="Etat de correction:", value="En cour...", inline=False)
    embed.set_footer(text=f"Bot V{BOT_VERSION}")
    embed.set_author(name="Rapport Automatique", icon_url=bot.user.avatar.url)
    view = discord.ui.View()
    item = discord.ui.Button(style=discord.ButtonStyle.green, label="Corriger", custom_id="bugreport_correction")
    view.add_item(item=item)
    item = discord.ui.Button(style=discord.ButtonStyle.grey, label="Non Recevable", custom_id="bugreport_correction_n")
    view.add_item(item=item)
    await channel.send(embed=embed, view=view)
    await ctx.reply(language("error_reported"))

try:
    bot.run(Bot.Token)
except:
    print("Bad Pasword")
os.system(f"python Launcher.py --bot {Bot.Name} --restart {r} --pasword {Bot.Pasword} {u}")
