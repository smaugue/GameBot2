import discord
from discord.ext import commands
from datetime import datetime

from Packs.automod import AutoMod
from Packs.interpretor import parse_actions
from Packs.Botloader import tz, Data, Bot


class MessageHandler(commands.Cog):
    """Gestion des messages (AutoMod + commandes custom)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        guild_language = Bot.get_language(Data.get_guild_conf(message.guild.id, Data.GUILD_LANGUAGE))

        # AutoMod
        blw, blws = {}, {}
        if message.content:
            if Data.get_guild_conf(message.guild.id, Data.AUTOMOD_ENABLE) == "1":
                level = Data.get_guild_conf(message.guild.id, Data.AUTOMOD_LEVEL) or 3
                blw, blws = AutoMod.check_message(message.content, level=level)
                v = AutoMod.automod_version()

        if blw:
            automod_channel_id = Data.get_guild_conf(message.guild.id, Data.AUTOMOD_CHANNEL)
            if automod_channel_id:
                channel = message.guild.get_channel(int(automod_channel_id))
                if channel:
                    zone = guild_language("spam_dm_report_title") if isinstance(message.channel, discord.channel.DMChannel) else guild_language("spam_dm_report_blocked_title")
                    start_time = datetime.strftime(datetime.now(tz), '%H:%M:%S')

                    embed = discord.Embed(title=zone, description=start_time, color=discord.Color.brand_red())
                    embed.set_thumbnail(url=message.author.avatar.url)
                    embed.add_field(name=guild_language("spam_dm_embed_user"), value=message.author.mention, inline=False)
                    embed.add_field(name=guild_language("spam_dm_embed_target"), value=message.jump_url, inline=False)
                    embed.add_field(name=guild_language("spam_dm_embed_message"), value=message.content, inline=False)
                    embed.add_field(name=guild_language("spam_dm_embed_status"), value=guild_language("spam_dm_status_pending"), inline=False)
                    embed.set_footer(text=guild_language("api_autmod_version").format(v=v))

                    # bouton de modération
                    view = discord.ui.View()
                    item = discord.ui.Button(style=discord.ButtonStyle.danger, label=guild_language("moderate_button"), custom_id="automod_action")
                    view.add_item(item=item)

                    for key in blw:
                        embed.add_field(
                            name=guild_language("spam_dm_embed_detected_word").format(word=key),
                            value=guild_language("spam_dm_embed_similarity").format(similarity=round(blws[key], 2) * 100, detected=blw[key]),
                            inline=False
                        )
                    if message.attachments:
                        for attachment in message.attachments:
                            embed.add_field(name=guild_language("spam_dm_embed_attachment"), value=attachment.proxy_url, inline=False)

                    await channel.send(embed=embed, view=view)

        # Commandes custom
        data = Data.get_guild_conf(message.guild.id, Data.CUSTOM_COMMANDS_NAMES)
        if data:
            commands_list = data.split("\n")
            ctx = await self.bot.get_context(message)
            message_content = message.content.strip()
            space_index = message_content.find(' ')
            command = message_content if space_index == -1 else message_content[:space_index]

            if command in commands_list:
                executor = Data.get_guild_conf(message.guild.id, command)
                try:
                    action_list = parse_actions(ctx, executor)
                    for action in action_list:
                        await action.execute(ctx)
                except Exception as e:
                    await ctx.send(guild_language("error_cusstom_commande").format(error=str(e)))
                    Bot.console("ERROR", e)


async def setup(bot: commands.Bot):
    await bot.add_cog(MessageHandler(bot))
