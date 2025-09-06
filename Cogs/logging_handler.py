# Cogs/logging_handler.py
import discord
from discord.ext import commands
from discord.ext.commands import Context

from Packs.Botloader import Bot, Data
from Packs.version import BOT_VERSION


class LoggingHandler(commands.Cog):
    """Gestion centralisée des logs et erreurs."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # === Logs des commandes (prefix + slash/hybride) === #
    async def log_command(self, ctx_or_inter: Context | discord.Interaction, command_name: str):
        if isinstance(ctx_or_inter, Context):  # Commande prefix
            author = ctx_or_inter.author
            guild = ctx_or_inter.guild
            raw_input = ctx_or_inter.message.content
        else:  # Slash ou hybride
            author = ctx_or_inter.user
            guild = ctx_or_inter.guild
            if ctx_or_inter.namespace:
                args_joined = " ".join(str(v) for v in vars(ctx_or_inter.namespace).values())
                raw_input = f"/{command_name} {args_joined}".strip()
            else:
                raw_input = f"/{command_name}"

        location = "[DM]" if guild is None else f"{guild.name} ({guild.id})"

        Bot.console(
            "INFO",
            f"Commande utilisée: <{raw_input}> "
            f"par {author} ({author.id}) "
            f"dans {location}"
        )

    # === Events liés aux commandes === #
    @commands.Cog.listener()
    async def on_command(self, ctx: Context):
        # Si c’est une commande hybride exécutée en slash,
        # ctx.interaction sera NON NULL → on laisse l’autre event gérer
        if ctx.interaction is not None:
            return  
    
        # Sinon (commande prefix pure ou hybride en prefix) → on log ici
        await self.log_command(ctx, ctx.command.qualified_name)
    
    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: discord.app_commands.Command):
        # Ne logge que les vrais slash / hybrides exécutés en slash
        await self.log_command(interaction, command.name)


    # === Gestion des erreurs globales === #
    @commands.Cog.listener()
    async def on_error(self, event_method, *args, **kwargs):
        error = kwargs.get('error')
        if not error:
            return
        guild = self.bot.get_guild(Bot.BotGuild)
        channel = guild.get_channel_or_thread(Bot.BugReportChannel)

        embed = discord.Embed(
            title="Rapport de Bug Global",
            description=f"Une erreur est survenue au niveau de: `{event_method}`.",
            colour=discord.Colour.orange()
        )
        embed.add_field(name="Bug:", value=f"```{error}```", inline=False)
        embed.add_field(name="Etat de correction:", value="En cour...", inline=False)
        embed.set_footer(text=f"Bot V{BOT_VERSION}")
        embed.set_author(name="Rapport Automatique", icon_url=self.bot.user.avatar.url)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.green, label="Corriger", custom_id="bugreport_correction"))
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.grey, label="Non Recevable", custom_id="bugreport_correction_n"))

        await channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error):
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

        guild = self.bot.get_guild(Bot.BotGuild)
        channel = guild.get_channel_or_thread(Bot.BugReportChannel)

        embed = discord.Embed(
            title="Rapport de Bug",
            description=f"Commande concernée `{command}`.",
            colour=discord.Colour.orange()
        )
        embed.add_field(name="Bug:", value=f"```{error}```", inline=False)
        embed.add_field(name="Etat de correction:", value="En cour...", inline=False)
        embed.set_footer(text=f"Bot V{BOT_VERSION}")
        embed.set_author(name="Rapport Automatique", icon_url=self.bot.user.avatar.url)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.green, label="Corriger", custom_id="bugreport_correction"))
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.grey, label="Non Recevable", custom_id="bugreport_correction_n"))

        await channel.send(embed=embed, view=view)
        await ctx.reply(language("error_reported"))


async def setup(bot: commands.Bot):
    await bot.add_cog(LoggingHandler(bot))
