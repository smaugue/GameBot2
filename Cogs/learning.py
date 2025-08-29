import discord
import asyncio
import os
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from Packs.Botloader import Bot, Utilitary
from random import randint, sample, shuffle

class VocabularyTest(discord.ui.View):
    def __init__(self, ctx: Context, correct: str, pron: str, options: list, lang: str):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.correct = correct
        self.pron = pron
        self.lang = lang
        self.result = None

        for option in options:
            button = discord.ui.Button(label=option, style=discord.ButtonStyle.primary, custom_id=option)
            button.callback = self.handle_button_click
            self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Vous n'êtes pas autorisé à répondre à cette question.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        if hasattr(self, 'message'):
            await self.message.edit(view=self)

    async def handle_button_click(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Vous n'êtes pas autorisé à répondre à cette question.", ephemeral=True)
            return

        tts = Utilitary.maketts(self.correct, self.lang, name=f"{self.pron}.mp3")
        print(tts)

        if interaction.data["custom_id"] == self.correct:
            self.result = True
            await interaction.response.send_message(f"Bonne réponse ! 🎉\n**{self.correct}** ({self.pron}).", ephemeral=True)
            await interaction.channel.send(file=discord.File(tts))
        else:
            self.result = False
            await interaction.response.send_message(f"Mauvaise réponse ! La bonne réponse était : **{self.correct}** ({self.pron}).", ephemeral=True)
            await interaction.channel.send(file=discord.File(tts))

        os.remove(tts)

        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        await interaction.message.edit(view=self)
        self.stop()

class Learning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="vocabulary")
    @commands.guild_only()
    async def world_reconize(self, ctx: Context, nombre):
        lang = "ja"
        d = {}
        mots = 0
        try:
            with open(f"Data/{lang}.txt", "r", encoding="utf-8") as voca:
                entete = voca.readline()
                fr, lg = entete.strip().split(",")
                for ligne in voca:
                    if "'''" in ligne:
                        while "'''" not in ligne:
                            pass
                    else:
                        quest, trad = ligne.strip().split("=")
                        trad, speak = trad.split(";")
                        mots += 1
                        d[quest] = trad, speak
        except Exception as e:
            await ctx.reply("Une erreur s'est produite.", ephemeral=True)
            Bot.console("ERROR", e)
            return

        if mots == 0:
            await ctx.reply(f"Aucun mot trouvé dans le test de {lang}.", ephemeral=True)
        else:
            embed = discord.Embed(
                title=f"Test de vocabulaire {lang}",
                description=f"{mots} mots recensés",
                color=discord.Colour.blue(),
            )
            embed.set_thumbnail(url="https://cdn3.emoji.gg/emojis/1041-zenitsu-yelena.png")
            if int(nombre) > mots:
                nombre = mots
                embed.add_field(
                    name="**Erreur:**",
                    value=f"**Le nombre de questions demandé est supérieur au nombre de mots recensés, vous n'aurez donc que {mots} questions.**",
                    inline=False,
                )
            embed.add_field(
                name="Règles:",
                value=f"""
                    Bienvenue {ctx.author.mention} sur le test de vocabulaire en {lang}.
                    Vous avez demandé un test de **{nombre} mots**.

                    Nous allons vous poser des questions avec **3 choix possibles** pour chaque mot. Veuillez répondre en cliquant sur le bouton correspondant à votre réponse. Un micro-bilan vous sera fourni après chaque réponse, et un bilan complet à la fin.

                    En cas d'échec ou d'erreur de la commande, veuillez contacter un administrateur.
                    """,   
                inline=True,
            )
            await ctx.send(embed=embed)

            j, f, total = 0, 0, 0
            fautes = []
            mots_list = list(d.items())

            for _ in range(int(nombre)):
                d = randint(1, mots - 2)
                print(d)
                question, (correct_trad, correct_pron) = mots_list[d]
                incorrects = sample([trad for key, (trad, _) in mots_list if key != question], 2)
                options = [correct_trad] + incorrects
                shuffle(options)

                view = VocabularyTest(ctx, correct_trad, correct_pron, options, lang)

                question_embed = discord.Embed(
                    title="Question:",
                    description=f"Quelle est la traduction du mot : **{question}** ?",
                    color=discord.Colour.orange(),
                )
                question_embed.set_footer(text=f"Langue: {lang}")
                view.message = await ctx.send(embed=question_embed, view=view)

                await view.wait()

                if view.result is True:
                    j += 1
                else:
                    f += 1
                    fautes.append(f"**{question}** : {correct_trad} ({correct_pron})")

            bilan_embed = discord.Embed(
                title="Bilan final",
                description=f"Test terminé pour {ctx.author.mention}.\n\n**Bonnes réponses :** {j}/{nombre}\n**Mauvaises réponses :** {f}/{nombre}",
                color=discord.Colour.green(),
            )
            if fautes:
                bilan_embed.add_field(
                    name="Réponses incorrectes",
                    value="\n".join(fautes),
                    inline=False,
                )
            await ctx.send(embed=bilan_embed)

async def setup(bot):
    await bot.add_cog(Learning(bot))