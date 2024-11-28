# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import discord
from discord import Embed, Colour
from discord.ui import Button, View

class EmbedGenerator:
    def __init__(self):
        pass

    def timeout_embed(self):
        embed = Embed(description=":hourglass:Timeout: délais d'attente de l'intéraction dépassé.", colour=discord.Colour.dark_gold())
        return embed

    def pages_embed(self, title: str, color: Colour, content: dict) -> list:
        """
        Génère des embeds paginés à partir d'un contenu donné.
        
        :param title: Titre de l'embed.
        :param color: Couleur de l'embed.
        :param content: Dictionnaire où chaque clé correspond au titre du field et chaque valeur au contenu.
        
        :return: Liste des objets embeds (chaque objet représentant une page).
        """
        embeds = []
        embed = Embed(title=title, colour=color)
        field_count = 0
        page_number = 1
        page_total = 0

        for key, value in content.items():
            embed.add_field(name=key, value=value, inline=False)
            field_count += 1

            if field_count == 1:
                page_total +=1

            if field_count >= 25:
                embeds.append(embed)
                embed = Embed(title=title, colour=color)
                field_count = 0

        if field_count > 0:
            embeds.append(embed)

        if len(embeds) != 1:
            for embed in embeds:
                embed.set_footer(text=f"{page_number}/{page_total}")
                page_number += 1

        return embeds

    async def send_paginated_embed(self, ctx, title: str, color: Colour, content: dict):
        """
        Envoie un embed paginé avec boutons de navigation si plus d'une page.
        
        :param ctx: Contexte de la commande.
        :param title: Titre de l'embed.
        :param color: Couleur de l'embed.
        :param content: Dictionnaire où chaque clé correspond au titre du field et chaque valeur au contenu.
        """
        pages = self.pages_embed(title=title, color=color, content=content)
        current_page = 0

        if len(pages) == 1:
            await ctx.send(embed=pages[0])
            return

        next_button = Button(label="▶️", style=discord.ButtonStyle.secondary)
        previous_button = Button(label="◀️", style=discord.ButtonStyle.secondary)

        def update_buttons():
            previous_button.disabled = current_page == 0
            next_button.disabled = current_page == len(pages) - 1

        async def next_page(interaction: discord.Interaction):
            nonlocal current_page
            if current_page < len(pages) - 1:
                current_page += 1
                update_buttons()
                await interaction.response.edit_message(embed=pages[current_page], view=view)

        async def previous_page(interaction: discord.Interaction):
            nonlocal current_page
            if current_page > 0:
                current_page -= 1
                update_buttons()
                await interaction.response.edit_message(embed=pages[current_page], view=view)
        next_button.callback = next_page
        previous_button.callback = previous_page
        view = View(timeout=180)
        view.add_item(previous_button)
        view.add_item(next_button)
        update_buttons()
        await ctx.send(embed=pages[current_page], view=view)

#timeout_embed = EmbedGenerator.timeout_embed()
