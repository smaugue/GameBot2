# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import discord
import os
import asyncio
from Packs.Botloader import Data, Bot
from Packs.automod import AutoMod
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from typing import List
from random import randint

class Privat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def voca_autocompletion(self, interaction: discord.Interaction,current: str) -> List[app_commands.Choice[str]]:
            langs = ['test']
            return [
                    app_commands.Choice(name=lang, value=lang)
                    for lang in langs if current.lower() in lang.lower()
                ]

    voca_user_data = {}
    ctx_mapping ={}
    
    @commands.hybrid_command(name = "voca")
    @app_commands.autocomplete(lang = voca_autocompletion)
    @commands.guild_only()
    async def testvoca(self, interaction: Context, lang: str, nombre: int):
        if Data.get_user_conf(interaction.guild.id, interaction.author.id, Data.key['testvoca']) == "1":
            return await Privat.test_voca_logic(self.bot, interaction, lang, nombre)
        else: return await Bot.on_refus_interaction(interaction)

    async def test_voca_logic(self, ctx: Context, lang, nombre):
        q = {}
        r = {}
        mots = 0
        try:
            with open(f"{lang}.txt", "r", encoding="utf-8") as voca:
                entete = voca.readline()
                fr, lg = entete.strip().split(",")
                for ligne in voca:
                    if "'''" in ligne:
                        while "'''" not in ligne:
                            pass
                    else:
                        quest, trad = ligne.strip().split(",")
                        mots += 1
                        q[mots] = quest
                        r[mots] = trad
        except Exception as e:
            await ctx.reply("Une erreur s'est produite.", ephemeral=True)
            Bot.console("ERROR", e)
            return
        if mots == 0:
            await ctx.reply(f"Aucun mot trouvé dans le test de {lang}.", ephemeral=True)
        else:
            embed = discord.Embed(title = f"Teste de vocabulaire {lang}", description = f"{mots} mots ressancés", color=discord.Colour.blue())
            embed.set_thumbnail(url = "https://cdn3.emoji.gg/emojis/1041-zenitsu-yelena.png")
            if int(nombre) > mots:
                nombre = mots
                embed.add_field(name="**Erreur:**", value=f"**Le nombre de questions demandé est supèrieur au nombre de mots ressancés, vous n'aurez donc que {mots} questions.**", inline=False)
            embed.add_field(name = "Règles:", value =  
                    f"""
                        Bienvenue {ctx.author.mention} sur le teste de vocabulaire d'{lang}.
                        Vous avez demandez un test de **{nombre} mots**.

                        Nous alons vous demander une à une les traduction de {nombre} mots pris au hazard dans une base de donnée de {mots} mots, pour y répondre veuillez envoyer votre réponse dans ce channel.
                        Après chaque réponse un microbilant vous est fournie, à la fin de la séssion un bilan complet.
                        En cas d'écheque ou d'erreure de la comande veuillez contacter un administrateur.
                        La vérification ignore les articles mais prend en compte les majuscules.

                        **IMPORTANT! Les eszetts (ß) serrons remplassé par "ss"**.
                        """
                    , inline = True)
            await ctx.channel.send(embed=embed)
            j, f, total = 0, 0, 0
            faut = []
            checked = []
            for i in range(int(nombre)):
                nbr = randint(1, mots)
                while nbr in checked:
                    nbr = randint(1, mots)
                checked.append(nbr)
                question = q[nbr]
                reponse = r[nbr]
                total = total + 1
                embed = discord.Embed(title = "Quelle est la traduction de", description = f"**{question}**", color=discord.Colour.dark_theme())
                embed.set_footer(text = f"Question: {total}/{nombre}")
                await ctx.channel.send(embed=embed)
                def checkMessage(message):
                    return ctx.author == message.author and ctx.channel == message.channel
                rep = await self.wait_for("message", check = checkMessage)
                if rep.content in reponse:
                    j, titre, color, url = j + 1, "Juste", discord.Colour.green(), "https://cdn3.emoji.gg/emojis/2990_yes.png"
                else:
                    faut.append(nbr)
                    f, titre, color, url = f + 1, "Faux", discord.Colour.red(), "https://cdn3.emoji.gg/emojis/1465-x.png"
                reu = j * 100 /total
                embed = discord.Embed(title = titre, description = 
                            f"""
                            La réponse est **{reponse}**
                            {int(reu)}% de réussite.
                            """, color=color)
                embed.set_thumbnail(url = url)
                await ctx.channel.send(embed=embed)
                try:
                    await ctx.channel.send(file=discord.File(Bot.maketts(reponse, lg, name=f"{reponse}.mp3")))
                    os.remove(f'{reponse}.mp3')
                except Exception as e:
                    Bot.console('WARN', e)
            note = j*20/total
            note = round(note, 1)
            reu = round(reu, 2)
            embed = discord.Embed(title = "Résultats", description = f"**{note}/20**", color=discord.Colour.from_rgb(255, 255, 255))
            embed.set_thumbnail(url = "https://cdn3.emoji.gg/emojis/3323-guilty.png")
            embed.add_field(name = "Remarque", value = 
                    f"""
                    Bravos, vous avez finit le test de vocabulaire!
                    Vous avez répondu juste à **{j}/{total}** questions.
                    Votre note est de **{note}/20**, soit **{reu}%** de réussite.
                    """
                    , inline = True)
            await ctx.channel.send(embed=embed)
            if len(faut) != 0:
                embed = discord.Embed(title="Révision", description="Liste de mots à réviser.", color=discord.Colour.blue())
                value = ""
                for nbr in faut:
                    value = f"{value}\n**{r[nbr]}**:\n{q[nbr]}"
                embed.add_field(name=f":sweat:", value=value, inline=False)
                await ctx.channel.send(embed=embed)
            class ActionSelector(discord.ui.View):
                def __init__(sf, ctx, timeout=60):
                    super().__init__(timeout=timeout)
                    sf.ctx = ctx
                    sf.message_button_disabled = False
                    sf.message = None
                @discord.ui.button(style=discord.ButtonStyle.blurple, label="Relancer le test", custom_id="restart_test")
                async def restart_button(sf, button: discord.ui.Button, interaction: discord.Interaction):
                    if not sf.message_button_disabled:
                        sf.message_button_disabled = True
                        button.disabled = True
                        await interaction.response.edit_message(view=sf)
                        await Privat.test_voca_logic(self, sf.ctx, lang, nombre)
                async def on_timeout(sf):
                    sf.message_button_disabled = True
                    for child in sf.children:
                        if isinstance(child, discord.ui.Button):
                            child.disabled = True
                    if sf.message:
                        await sf.message.edit(view=sf)
            view = ActionSelector(ctx, 60)
            view.message = await ctx.channel.send(view=view)

    #spam commande
    @commands.hybrid_command(name="dm")
    @commands.guild_only()
    async def dm(self, ctx: Context, mention: discord.User,*,msg):
        blw, blws = AutoMod.check_message(msg)
        if len(blw) != 0:
            return await Bot.on_refus_interaction(ctx)
        member_blackliste = Data.get_user_conf(ctx.guild.id, mention.id, Data.DM_BLACKLISTE)
        if member_blackliste is not None:
            if str(ctx.author.id) in member_blackliste:
                return await ctx.reply(f"Le message a été exprécément refusé par {mention.mention}.")
        if Data.get_guild_conf(ctx.guild.id, Data.AUTOMOD_CHANNEL):
            print(Data.get_user_conf(ctx.guild.id, ctx.author.id, Data.key['dm']))
            if Data.get_user_conf(ctx.guild.id, ctx.author.id, Data.key['dm']) == "1":
                message = ctx.message
                if len(message.attachments) > 1:
                    return await ctx.reply("Vous ne pouvez envoyer qu'un seul fichier à la fois.")
                try:
                    channel = await mention.create_dm()
                except discord.Forbidden: ctx.reply("Impossible d'envoyer le message.", ephemeral=True)
                embed = discord.Embed(title = "**Message**", description = msg, color=discord.Colour.dark_magenta())
                embed.set_author(name = f"{ctx.author.name} (id:{ctx.author.id})", icon_url = ctx.author.avatar)
                view = discord.ui.View()
                item = discord.ui.Select(
                custom_id='spam_dm',
                placeholder="Signaler un Spam",
                options=[
                    discord.SelectOption(label="Signaler", value=f"n/|/{ctx.guild.id}/|/{ctx.author.id}/|/{msg}"),
                    discord.SelectOption(label="Signaler et Bloquer (action irréversible)", value=f"y/|/{ctx.guild.id}/|/{ctx.author.id}/|/{msg}")
                ]
            )
                view.add_item(item=item)
                if message.attachments :
                    for attachment in message.attachments:
                        embed.set_image(url= attachment.url)
                        await channel.send(embed=embed, view=view)
                else:
                    await channel.send(embed=embed ,view=view)
                return await ctx.reply("Succès", ephemeral=True) 
            return await Bot.on_refus_interaction(ctx)
        else: return await ctx.reply("Le serveur ne possède pas la configuration requise pour l'exécution de la commande.")