# Cogs/interaction_handler.py
import discord
from discord.ext import commands
from datetime import datetime
from Packs.Botloader import Bot, Data, owner_permission, tz


class InteractionHandler(commands.Cog):
    """Gestion centralisée des interactions (boutons, menus, etc.)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # === Utils Embed / Views === #
    @staticmethod
    def make_embed(title: str, description: str, color=discord.Color.red()):
        return discord.Embed(title=title, description=description, color=color)

    @staticmethod
    def make_button(style, label, custom_id, disabled=False):
        view = discord.ui.View()
        view.add_item(discord.ui.Button(style=style, label=label, custom_id=custom_id, disabled=disabled))
        return view

    @staticmethod
    def make_select(custom_id, placeholder, disabled=False):
        view = discord.ui.View()
        view.add_item(
            discord.ui.Select(
                custom_id=custom_id,
                placeholder=placeholder,
                options=[discord.SelectOption(label="empty", value="empty")],
                disabled=disabled
            )
        )
        return view

    # === Gestion des interactions === #
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Router des interactions custom_id → handler"""
        if not interaction.data or "custom_id" not in interaction.data:
            return

        cid = interaction.data["custom_id"]

        # Mapping des handlers
        handlers = {
            "spam_dm": self.handle_spam_dm,
            "bugreport_correction": self.handle_bugreport_correction,
            "bugreport_correction_n": self.handle_bugreport_correction_n,
            "automod_action": self.handle_automod_action,
        }

        handler = handlers.get(cid)
        if handler:
            await interaction.response.defer()
            await handler(interaction)

    # === Handlers === #
    async def handle_spam_dm(self, interaction: discord.Interaction):
        b, guild, user, msg = interaction.data["values"][0].split("/|/")
        guild_language = Bot.get_language(Data.get_guild_conf(int(guild), Data.GUILD_LANGUAGE))

        if b == "y":
            blackliste = Data.get_user_conf(guild, interaction.user.id, Data.DM_BLACKLISTE) or ""
            blackliste += f"\n{user}"
            Data.set_user_conf(guild, interaction.user.id, Data.DM_BLACKLISTE, blackliste)
            title = guild_language("spam_dm_report_blocked_title_oni")
            placeholder = guild_language("spam_dm_report_blocked_placeholde_onir")
        else:
            title = guild_language("spam_dm_report_title")
            placeholder = guild_language("spam_dm_report_placeholder")

        automod_channel_id = Data.get_guild_conf(guild, Data.AUTOMOD_CHANNEL)
        try:
            channel = self.bot.get_guild(int(guild)).get_channel(int(automod_channel_id))
        except Exception as e:
            error_message = guild_language("error_admin_contact", guild=guild, error=e)
            return await interaction.channel.send(error_message)

        start_time = datetime.strftime(datetime.now(tz), "%H:%M:%S")
        embed = self.make_embed(
            guild_language("spam_dm_embed_title"), start_time, discord.Color.brand_red()
        )
        embed.add_field(name=guild_language("spam_dm_embed_user"), value=self.bot.get_user(int(user)).mention, inline=False)
        embed.add_field(name=guild_language("spam_dm_embed_target"), value=interaction.user.mention, inline=False)
        embed.add_field(name=guild_language("spam_dm_embed_message"), value=msg, inline=False)
        embed.add_field(name=guild_language("spam_dm_embed_status"), value=guild_language("spam_dm_status_pending"), inline=False)
        embed.add_field(name=guild_language("spam_dm_embed_measure"), value=placeholder, inline=False)

        await channel.send(embed=embed, view=self.make_button(discord.ButtonStyle.danger, guild_language("moderate_button"), "automod_action"))

        # Désactiver le menu original
        await interaction.message.edit(view=self.make_select("spam_dm", placeholder, disabled=True))

        # Feedback à l’utilisateur
        feedback = self.make_embed(title, title, discord.Colour.red())
        return await interaction.channel.send(embed=feedback)

    async def handle_bugreport_correction(self, interaction: discord.Interaction):
        if interaction.user.id != owner_permission.owner_id:
            return
        guild_language = Bot.get_language(Data.get_guild_conf(interaction.guild.id, Data.GUILD_LANGUAGE))

        embed = interaction.message.embeds[0]
        embed.set_field_at(1, name=embed.fields[1].name, value=guild_language("correction_done"), inline=embed.fields[1].inline)
        embed.color = discord.Color.green()

        return await interaction.message.edit(embed=embed, view=self.make_button(discord.ButtonStyle.gray, guild_language("bugreport_corrected_button"), "bugreport_correction", True))

    async def handle_bugreport_correction_n(self, interaction: discord.Interaction):
        if interaction.user.id != owner_permission.owner_id:
            return
        guild_language = Bot.get_language(Data.get_guild_conf(interaction.guild.id, Data.GUILD_LANGUAGE))

        embed = interaction.message.embeds[0]
        embed.set_field_at(1, name=embed.fields[1].name, value=guild_language("bugreport_correction_not_receivable"), inline=embed.fields[1].inline)
        embed.color = discord.Color.dark_gray()

        return await interaction.message.edit(embed=embed, view=self.make_button(discord.ButtonStyle.gray, guild_language("bugreport_not_receivable_button"), "bugreport_correction_n", True))

    async def handle_automod_action(self, interaction: discord.Interaction):
        guild_language = Bot.get_language(Data.get_guild_conf(interaction.guild.id, Data.GUILD_LANGUAGE))

        embed = interaction.message.embeds[0]
        embed.set_field_at(3, name=embed.fields[3].name, value=guild_language("moderated_by", user=interaction.user.mention), inline=embed.fields[1].inline)
        embed.color = discord.Color.dark_red()

        return await interaction.message.edit(embed=embed, view=self.make_button(discord.ButtonStyle.success, guild_language("moderated_button"), "automod_action", True))


async def setup(bot: commands.Bot):
    await bot.add_cog(InteractionHandler(bot))
