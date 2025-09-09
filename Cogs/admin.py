# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import discord
import asyncio
import aiohttp
from Packs.Botloader import Data, Bot
from discord.ui import View, Select
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from typing import List
from Packs.interpretor import parse_actions

# Pour réduire la consommation de RAM, nous définissons la liste des commandes en variable de classe
BLACKLIST_COMMANDS = ['sayic', 'say', 'dm', 'vtts', 'ftts', 'random', 'execute']
SRVCONF_PARAMETERS = ['automod_channel']

class Admin(commands.Cog):
    __slots__ = ('bot',)
    
    def __init__(self, bot):
        self.bot = bot

    async def blackliste_autocompletion(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=cmd, value=cmd)
            for cmd in BLACKLIST_COMMANDS if current.lower() in cmd.lower()
        ]
    
    async def srvconf_autocompletion(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=param, value=param)
            for param in SRVCONF_PARAMETERS if current.lower() in param.lower()
        ]

    @commands.hybrid_command(name="blackliste")
    @commands.has_permissions(administrator=True)
    @app_commands.autocomplete(cmd=blackliste_autocompletion)
    @commands.guild_only()
    async def blackliste(self, ctx: Context, member: discord.Member, cmd: str, permission: bool):
        # Mise en cache de la langue
        guild_conf = Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE)
        language = Bot.get_language(guild_conf)
        if cmd not in Data.key_value:
            return await ctx.reply(language("invalid_key"), ephemeral=True)
        var_key = Data.key_value[cmd]
        data = Data.get_user_conf(ctx.guild.id, ctx.author.id, var_key)
        try:
            Data.set_user_conf(ctx.guild.id, member.id, var_key, permission)
            msg = language("blacklist_add_member_befor").format(member=member, cmd=cmd, data=data) if data is not None \
                  else language("blacklist_add_member").format(member=member, cmd=cmd)
            return await ctx.reply(msg)
        except Exception as e:
            return await ctx.reply(language("error").format(e=e))

    @commands.hybrid_command(name="clear", help="Supprime les n derniers messages dans le canal.\nSyntaxe: `{prefix}clear [nombre]`")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def clear(self, ctx: Context, amount: int):
        guild_conf = Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE)
        language = Bot.get_language(guild_conf)
        await ctx.defer()
        try:
            await ctx.channel.purge(limit=amount)
            return await ctx.reply(language("clear_success"), ephemeral=True)
        except ValueError:
            return await ctx.reply(language("clear_invalid_amount"), ephemeral=True)
        except discord.NotFound:
            return await ctx.reply(language("clear_not_found"), ephemeral=True)

    @commands.hybrid_command(name="automod")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def automod_enable(self, ctx: Context, enable: bool):
        guild_conf = Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE)
        language = Bot.get_language(guild_conf)
        try:
            Data.set_guild_conf(ctx.guild.id, Data.AUTOMOD_ENABLE, enable)
            return await ctx.reply(language("automod_enable") if enable else language("automod_disable"))
        except Exception as e:
            return await ctx.reply(language("error").format(e=e))

    @commands.hybrid_command(name="automod_channel")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def automod_channel(self, ctx: Context, channel: discord.TextChannel):
        guild_conf = Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE)
        language = Bot.get_language(guild_conf)
        old_data = Data.get_guild_conf(ctx.guild.id, Data.AUTOMOD_CHANNEL)
        try:
            Data.set_guild_conf(ctx.guild.id, Data.AUTOMOD_CHANNEL, channel.id)
            msg = language("automod_channel_updated").format(old_channel=old_data, new_channel=channel) \
                  if old_data is not None else language("automod_channel_set").format(channel=channel)
            return await ctx.reply(msg)
        except Exception as e:
            return await ctx.reply(language("error").format(e=e))

    @commands.hybrid_command(name="automod_level", help="Définit la sensibilité de l'automod : 1 = insultes graves uniquement, 3 = langage grossier inclus.")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def automod_level(self, ctx: Context, level: int = 3):
        guild_conf = Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE)
        language = Bot.get_language(guild_conf)
        old_level = Data.get_guild_conf(ctx.guild.id, Data.AUTOMOD_LEVEL)
        try:
            Data.set_guild_conf(ctx.guild.id, Data.AUTOMOD_LEVEL, level)
            msg = language("automod_level_updated").format(old_level=old_level, new_level=level) \
                  if old_level is not None else language("automod_level_set").format(level=level)
            return await ctx.reply(msg)
        except Exception as e:
            return await ctx.reply(language("error").format(e=e))

    @commands.hybrid_command(name="guild_language", help="Définit la langue de la guilde.")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def guild_language(self, ctx: Context, lang: str = "en"):
        guild_conf = Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE)
        language = Bot.get_language(guild_conf)
        old_lang = Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE)
        try:
            Data.set_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE, lang)
            msg = language("language_updated").format(old_lang=old_lang, new_lang=lang) \
                  if old_lang is not None else language("language_set").format(lang=lang)
            return await ctx.reply(msg)
        except Exception as e:
            return await ctx.reply(language("error").format(e=e))
        
    @commands.hybrid_command(name="execute")
    @commands.guild_only()
    async def execute(self, ctx: Context, *, actions: str):
        if Data.get_user_conf(ctx.guild.id, ctx.author.id, Data.key_value['execute']) == "1":
            try:
                for action in parse_actions(ctx, actions):
                    await action.execute(ctx)
            except Exception as e:
                await ctx.send(f"Error: {str(e)}")
                Bot.console('ERROR', e)
        else:
            await Bot.on_refus_interaction(ctx)

    @commands.hybrid_command(name="create_command")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def create_command(self, ctx: commands.Context, prefix: str, name: str):
        guild_conf = Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE)
        language = Bot.get_language(guild_conf)
        data = Data.get_guild_conf(ctx.guild.id, Data.CUSTOM_COMMANDS_NAMES) or ""
        cmds = [cmd for cmd in data.split("\n") if cmd.strip()] if data else []
        if len(cmds) > 4:
            return await ctx.reply(language("max_custom_commands_reached"))
        executore = "Start{}"
        embed = discord.Embed(
            title=language("custom_command_title"),
            description=name,
            color=discord.Colour.dark_magenta()
        )
        embed.add_field(name=language("prefix_label"), value=prefix)
        command_name = f"{prefix}{name}"

        # Définition d'une vue avec __slots__ pour limiter la taille mémoire
        class ActionSelector(View):
            __slots__ = ('bot', 'embed', 'data', 'executore',
                         'script_button_disabled', 'message_button_disabled',
                         'image_button_disabled', 'ok_button_disabled')
            def __init__(self, bot, data, executore):
                super().__init__(timeout=60)
                self.bot = bot
                self.embed = embed
                self.data = data
                self.executore = executore
                self.script_button_disabled = False
                self.message_button_disabled = False
                self.image_button_disabled = False
                self.ok_button_disabled = False
 
            @discord.ui.button(style=discord.ButtonStyle.blurple, label="Script", custom_id="script")
            async def script_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                button, interaction = interaction, button  # Correction de l'ordre des paramètres
                if not self.script_button_disabled:
                    self.script_button_disabled = True
                    button.disabled = True
                    await interaction.response.edit_message(embed=self.embed, view=self)
                    prompt = await interaction.channel.send(language("script_prompt").format(user=interaction.user.mention))
                    try:
                        user_message = await self.bot.wait_for(
                            "message",
                            timeout=60,
                            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
                        )
                        self.embed.add_field(name=language("script_label"), value=user_message.content, inline=False)
                        self.executore += f"&{user_message.content}"
                        await interaction.edit_original_response(embed=self.embed, view=self)
                        await user_message.delete()
                        await prompt.delete()
                    except asyncio.TimeoutError:
                        await interaction.followup.send(language("timeout_message"))
            
            

            @discord.ui.button(style=discord.ButtonStyle.blurple, label=language("send_message_button"), custom_id="message")
            async def send_message_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                button, interaction = interaction, button  # Correction de l'ordre des paramètres
                if not self.message_button_disabled:
                    self.message_button_disabled = True
                    button.disabled = True
                    await interaction.response.edit_message(embed=self.embed, view=self)
                    prompt = await interaction.channel.send(language("message_prompt").format(user=interaction.user.mention))
                    try:
                        user_message = await self.bot.wait_for(
                            "message",
                            timeout=60,
                            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
                        )
                        self.embed.add_field(name=language("message_label"), value=user_message.content, inline=False)
                        self.executore += f"&SendMessage{{{user_message.content}}}"
                        await interaction.edit_original_response(embed=self.embed, view=self)
                        await user_message.delete()
                        await prompt.delete()
                    except asyncio.TimeoutError:
                        await interaction.followup.send(language("timeout_message"))

            @discord.ui.button(style=discord.ButtonStyle.green, label=language("send_image_button"), custom_id="image")
            async def send_image_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                button, interaction = interaction, button  # Correction de l'ordre des paramètres
                if not self.image_button_disabled:
                    self.image_button_disabled = True
                    button.disabled = True
                    await interaction.response.edit_message(embed=self.embed, view=self)
                    prompt = await interaction.channel.send(language("image_prompt").format(user=interaction.user.mention))
                    try:
                        user_message = await self.bot.wait_for(
                            "message",
                            timeout=60,
                            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
                        )
                        url = user_message.content
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url) as response:
                                if response.status == 200:
                                    self.executore += f"&SendImage{{{url}}}"
                                    self.embed.add_field(name=language("image_label"), value=url, inline=False)
                                    await interaction.edit_original_response(embed=self.embed, view=self)
                                    await user_message.delete()
                                    await prompt.delete()
                                else:
                                    await ctx.reply(language("image_not_found"))
                                    self.image_button_disabled = False
                                    button.disabled = False
                                    await interaction.edit_original_response(embed=self.embed, view=self)
                    except aiohttp.ClientConnectorError:
                        await ctx.reply(language("invalid_url"))
                        self.image_button_disabled = False
                        button.disabled = False
                        await interaction.edit_original_response(embed=self.embed, view=self)
                    except asyncio.TimeoutError:
                        await interaction.followup.send(language("timeout_message"))

            @discord.ui.button(style=discord.ButtonStyle.gray, label=language("finish_button"), custom_id="ok")
            async def ok_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                button, interaction = interaction, button  # Correction de l'ordre des paramètres
                if not self.ok_button_disabled:
                    self.ok_button_disabled = True
                    button.disabled = True
                    for item in self.children:
                        if isinstance(item, discord.ui.Button):
                            item.disabled = True
                    self.embed.add_field(name="Executor:", value=self.executore, inline=False)
                    await interaction.edit_original_response(embed=self.embed, view=self)
                    new_data = "\n".join(self.data) if self.data else ""
                    new_data = new_data + "\n" + command_name
                    Data.set_guild_conf(ctx.guild.id, Data.CUSTOM_COMMANDS_NAMES, new_data)
                    Data.set_guild_conf(ctx.guild.id, command_name, self.executore)
                    await ctx.send(language("command_saved"))

        view = ActionSelector(self.bot, cmds, executore)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="custom_commands")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def custom_commands(self, ctx: commands.Context):
        bot_inst = self.bot
        guild_conf = Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE)
        language = Bot.get_language(guild_conf)
        data = Data.get_guild_conf(ctx.guild.id, Data.CUSTOM_COMMANDS_NAMES) or ""
        embed = discord.Embed(
            title=language("custom_commands_title"),
            description=language("custom_commands_description"),
            color=discord.Colour.dark_magenta()
        )
        commands_list = [cmd for cmd in data.split("\n") if cmd.strip()] if data else []
        if not commands_list:
            embed.add_field(name=language("no_custom_commands"), value=language("create_command_hint"), inline=False)
            return await ctx.reply(embed=embed)

        for cmd in commands_list:
            # Ajouter directement la valeur en évitant de créer une copie
            embed.add_field(name=cmd, value=Data.get_guild_conf(ctx.guild.id, cmd), inline=False)

        class CommandSelect(Select):
            __slots__ = ('selected_command',)
            def __init__(self, cmds):
                options = [discord.SelectOption(label=cmd, description=f"Select {cmd}") for cmd in cmds]
                super().__init__(placeholder=language("select_command_placeholder"), min_values=1, max_values=1, options=options)
                self.selected_command = None
            async def callback(self, interaction: discord.Interaction):
                self.selected_command = self.values[0]
                self.view.stop()

        class CommandSelectView(View):
            __slots__ = ('command_select',)
            def __init__(self, cmds, timeout=60):
                super().__init__(timeout=timeout)
                self.command_select = CommandSelect(cmds)
                self.add_item(self.command_select)
            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)

        view = CommandSelectView(commands_list)
        view.message = await ctx.reply(embed=embed, view=view)
        await view.wait()
        selected_command = view.command_select.selected_command
        if selected_command:
            class ActionSelector(View):
                __slots__ = ('bot', 'selected_command', 'embed', 'data')
                def __init__(self, bot, selected_command, embed, data, timeout=60):
                    super().__init__(timeout=timeout)
                    self.bot = bot
                    self.selected_command = selected_command
                    self.embed = embed
                    self.data = data
                @discord.ui.button(style=discord.ButtonStyle.red, label=language("delete_button_label").format(cmd=selected_command), custom_id="delete_command")
                async def delete_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                    button, interaction = interaction, button  # Correction de l'ordre des paramètres
                    button.disabled = True
                    for item in self.children:
                        if isinstance(item, discord.ui.Button):
                            item.disabled = True
                    await interaction.edit_original_response(embed=self.embed, view=self)
                    await ctx.reply(language("confirm_deletion").format(cmd=selected_command), ephemeral=True)
                    try:
                        user_message = await self.bot.wait_for(
                            "message",
                            timeout=60,
                            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
                        )
                        if user_message.content.lower() == "delete":
                            self.data.remove(selected_command)
                            data_str = "\n".join(self.data)
                            Data.set_guild_conf(ctx.guild.id, Data.key_value['custom_commands_names'], data_str)
                            Data.delete_guild_conf(ctx.guild.id, selected_command)
                            await user_message.reply(language("deletion_success").format(cmd=selected_command))
                        elif user_message.content.lower() == "cancel":
                            await user_message.reply(language("deletion_cancelled"))
                        else:
                            await user_message.reply(language("deletion_invalid_command"))
                        await user_message.delete()
                    except asyncio.TimeoutError:
                        await ctx.send(language("timeout_message"))
                @discord.ui.button(style=discord.ButtonStyle.gray, label=language("cancel_button_label"), custom_id="ok")
                async def ok_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                    button, interaction = interaction, button  # Correction de l'ordre des paramètres
                    button.disabled = True
                    for item in self.children:
                        if isinstance(item, discord.ui.Button):
                            item.disabled = True
                    await interaction.edit_original_response(embed=self.embed, view=self)
            await view.message.edit(embed=embed, view=ActionSelector(bot_inst, selected_command, embed, commands_list))
        else:
            await ctx.send(language("timeout_message"))

async def setup(bot):
    await bot.add_cog(Admin(bot))