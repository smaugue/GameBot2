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

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def blackliste_autocompletion(self, interaction: discord.Interaction,current: str) -> List[app_commands.Choice[str]]:
        commands = ['sayic', 'say', 'dm', 'vtts', 'ftts', 'random', 'execute']
        return [
                app_commands.Choice(name=cmd, value=cmd)
                for cmd in commands if current.lower() in cmd.lower()
            ]
    
    async def srvconf_autocompletion(self, interaction: discord.Interaction,current: str) -> List[app_commands.Choice[str]]:
        parametres = ['automod_channel']
        return [
                app_commands.Choice(name=parametre, value=parametre)
                for parametre in parametres if current.lower() in parametre.lower()
            ]

    @commands.hybrid_command(name="blackliste")
    @commands.has_permissions(administrator = True)
    @app_commands.autocomplete(cmd = blackliste_autocompletion)
    @commands.guild_only()
    async def blackliste(self, ctx: Context, member: discord.Member, cmd, permission: bool):
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        if cmd not in Data.key:
            return await ctx.reply(language("invalid_key"), ephemeral=True)
        var_key =Data.key[cmd]
        data = Data.get_user_conf(ctx.guild.id, ctx.author.id, var_key)
        if data is not None:
            try:
                Data.set_user_conf(ctx.guild.id,member.id,var_key,permission)
                return await ctx.reply(language("blacklist_add_member_befor").format(member=member, cmd=cmd, data=data))
            except Exception as e:
                return await ctx.reply(language("error").format(e=e))
        try:
            Data.set_user_conf(guild_id=ctx.guild.id, user_id=member.id, conf_key=var_key, conf_value=permission)
            return await ctx.reply(language("blacklist_add_member").format(member=member, cmd=cmd))
        except Exception as e:
            return await ctx.reply(language("error").format(e=e))
        
    @commands.hybrid_command(name="clear", help="Supprime les n derniers messages dans le canal.\nSyntaxe: `{prefix}clear [nombre]`")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def clear(self, ctx: Context, amount: int):
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        await ctx.defer()
        try:
            await ctx.channel.purge(limit=int(amount))
            return await ctx.reply(language("clear_success"), ephemeral=True)
        except ValueError:
            return await ctx.reply(language("clear_invalid_amount"), ephemeral=True)
        except discord.NotFound:
            return await ctx.reply(language("clear_not_found"), ephemeral=True)

    @commands.hybrid_command(name="automod")
    @commands.has_permissions(administrator = True)
    @commands.guild_only()
    async def automod_enable(self, ctx: Context, enable:bool):
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        data = Data.get_guild_conf(ctx.guild.id, Data.AUTOMOD_ENABLE)
        if data is not None:
            try:
                Data.set_guild_conf(ctx.guild.id, Data.AUTOMOD_ENABLE, enable)
                if enable:
                    return await ctx.reply(language("automod_enable"))
                else:
                    return await ctx.reply(language("automod_disable"))
            except Exception as e:
                return await ctx.reply(language("error").format(e=e))
        try:
            Data.set_guild_conf(ctx.guild.id, Data.AUTOMOD_ENABLE, enable)
            if enable:
                return await ctx.reply(language("automod_enable"))
            else:
                return await ctx.reply(language("automod_disable"))
        except Exception as e:
            return await ctx.reply(language("error").format(e=e))

    @commands.hybrid_command(name="automod_channel")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def automod_channel(self, ctx: Context, channel: discord.TextChannel):
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        data = Data.get_guild_conf(ctx.guild.id, Data.AUTOMOD_CHANNEL)
        if data is not None:
            try:
                Data.set_guild_conf(ctx.guild.id, Data.AUTOMOD_CHANNEL, channel.id)
                return await ctx.reply(language("automod_channel_updated").format(old_channel=data, new_channel=channel))
            except Exception as e:
                return await ctx.reply(language("error").format(e=e))
        try:
            Data.set_guild_conf(ctx.guild.id, Data.AUTOMOD_CHANNEL, channel.id)
            return await ctx.reply(language("automod_channel_set").format(channel=channel))
        except Exception as e:
            return await ctx.reply(language("error").format(e=e))

    @commands.hybrid_command(name="automod_level", help="Définit la sensibilité de l'automod : 1 = insultes graves uniquement, 3 = langage grossier inclus.")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def automod_level(self, ctx: Context, level=3):
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        data = Data.get_guild_conf(ctx.guild.id, Data.AUTOMOD_LEVEL)
        if data is not None:
            try:
                Data.set_guild_conf(ctx.guild.id, Data.AUTOMOD_LEVEL, level)
                return await ctx.reply(language("automod_level_updated").format(old_level=data, new_level=level))
            except Exception as e:
                return await ctx.reply(language("error").format(e=e))
        try:
            Data.set_guild_conf(ctx.guild.id, Data.AUTOMOD_LEVEL, level)
            return await ctx.reply(language("automod_level_set").format(level=level))
        except Exception as e:
            return await ctx.reply(language("error").format(e=e))

    @commands.hybrid_command(name="guild_language", help="Définit la langue de la guilde.")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def guild_language(self, ctx: Context, lang="en"):
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        data = Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE)
        if data is not None:
            try:
                Data.set_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE, lang)
                return await ctx.reply(language("language_updated").format(old_lang=data, new_lang=lang))
            except Exception as e:
                return await ctx.reply(language("error").format(e=e))
        try:
            Data.set_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE, lang)
            return await ctx.reply(language("language_set").format(lang=lang))
        except Exception as e:
            return await ctx.reply(language("error").format(e=e))

    
    @commands.hybrid_command(name="execute")
    @commands.guild_only()
    async def execute(self, ctx: Context,*,actions: str):
        if Data.get_user_conf(ctx.guild.id, ctx.author.id, Data.key_value['execute']) == "1":
            try:
                action_list = parse_actions(ctx, actions)
                for action in action_list:
                    await action.execute(ctx)
            except Exception as e:
                await ctx.send(f"Error: {str(e)}")
                Bot.console('ERROR', e)
        else: await Bot.on_refus_interaction(ctx)

    @commands.hybrid_command(name="create_command")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def create_command(self, ctx: commands.Context, prefix: str, name: str):
        # Initialisation
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        data = Data.get_guild_conf(ctx.guild.id, Data.CUSTOM_COMMANDS_NAMES)
        if data and len(data) > 0:
            data = data.split("\n")
            if len(data) > 4:
                return await ctx.reply(language("max_custom_commands_reached"))
        executore = "Start{}"
        embed = discord.Embed(
            title=language("custom_command_title"),
            description=name,
            color=discord.Colour.dark_magenta()
        )
        embed.add_field(name=language("prefix_label"), value=prefix)
        bot = self.bot
        command_name = f"{prefix}{name}"

        # Classe pour gérer les interactions
        class ActionSelector(discord.ui.View):
            def __init__(self, bot, timeout=60):
                super().__init__(timeout=timeout)
                self.bot = bot
                self.embed = embed
                self.data = data
                self.executore = executore
                self.message_button_disabled = False
                self.image_button_disabled = False
                self.ok_button_disabled = False

            @discord.ui.button(style=discord.ButtonStyle.blurple, label=language("send_message_button"), custom_id="message")
            async def send_message_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                button, interaction = interaction, button
                if not self.message_button_disabled:
                    self.message_button_disabled = True
                    button.disabled = True
                    await interaction.response.edit_message(embed=self.embed, view=self)

                    prompt = await interaction.channel.send(language("message_prompt").format(user=interaction.user.mention))
                    try:
                        user_message = await bot.wait_for(
                            "message",
                            timeout=60,
                            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
                        )
                        self.embed.add_field(name=language("message_label"), value=user_message.content, inline=False)
                        self.executore = f"{self.executore}&SendMessage{{{user_message.content}}}"
                        await interaction.edit_original_response(embed=self.embed, view=self)
                        await user_message.delete()
                        await prompt.delete()
                    except asyncio.TimeoutError:
                        await interaction.followup.send(language("timeout_message"))

            @discord.ui.button(style=discord.ButtonStyle.green, label=language("send_image_button"), custom_id="image")
            async def send_image_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                button, interaction = interaction, button
                if not self.image_button_disabled:
                    self.image_button_disabled = True
                    button.disabled = True
                    await interaction.response.edit_message(embed=self.embed, view=self)

                    prompt = await interaction.channel.send(language("image_prompt").format(user=interaction.user.mention))
                    try:
                        user_message = await bot.wait_for(
                            "message",
                            timeout=60,
                            check=lambda m: m.author == interaction.user and m.channel == interaction.channel
                        )
                        url = user_message.content
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url) as response:
                                if response.status == 200:
                                    self.executore = f"{self.executore}&SendImage{{{url}}}"
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
                button, interaction = interaction, button
                if not self.ok_button_disabled:
                    self.ok_button_disabled = True
                    button.disabled = True
                    for item in self.children:
                        if isinstance(item, discord.ui.Button):
                            item.disabled = True
                    self.embed.add_field(name="Executor:", value=self.executore, inline=False)
                    await interaction.edit_original_response(embed=self.embed, view=self)
                    if self.data:
                        if command_name in self.data:
                            return await ctx.send(language("command_already_exists"))
                        data_str = "\n".join(self.data)
                    else:
                        data_str = ""
                    data = data_str + "\n" + command_name
                    Data.set_guild_conf(ctx.guild.id, Data.CUSTOM_COMMANDS_NAMES, data)
                    Data.set_guild_conf(ctx.guild.id, command_name, self.executore)
                    return await ctx.send(language("command_saved"))

        view = ActionSelector(self.bot)
        await ctx.send(embed=embed, view=view)

    
    @commands.hybrid_command(name="custom_commands")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def custom_commands(self, ctx: commands.Context):
        bot = self.bot
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        data = Data.get_guild_conf(ctx.guild.id, Data.CUSTOM_COMMANDS_NAMES)
        embed = discord.Embed(title=language("custom_commands_title"),description=language("custom_commands_description"),color=discord.Colour.dark_magenta())
        commands_list = None
        if data and len(data) > 0:
            data = data.split("\n")
            for command in data:
                commands_list = []
                commands_list.append(command)
                embed.add_field(name=command, value=Data.get_guild_conf(ctx.guild.id, command), inline=False)
        else:
            embed.add_field(name=language("no_custom_commandes"),value=language("create_command_hint"),inline=False)
            return await ctx.reply(embed=embed)

        class CommandSelect(Select):
            def __init__(self, commands):
                options = [discord.SelectOption(label=cmd, description=f"Select {cmd}") for cmd in commands]
                super().__init__(placeholder=language("select_command_placeholder"), min_values=1, max_values=1, options=options)
                self.selected_command = None
            async def callback(self, interaction: discord.Interaction):
                self.selected_command = self.values[0]
                self.view.stop()
        class CommandSelectView(View):
            def __init__(self, commands, timeout=60):
                super().__init__(timeout=timeout)
                self.command_select = CommandSelect(commands)
                self.add_item(self.command_select)
            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)
        if commands_list:
            view = CommandSelectView(commands_list)
            message = view.message = await ctx.reply(embed=embed, view=view)
            await view.wait()
            selected_command = view.command_select.selected_command
            if selected_command:
                class ActionSelector(View):
                    def __init__(self, bot, selected_command, timeout=60):
                        super().__init__(timeout=timeout)
                        self.bot = bot
                        self.selected_command = selected_command
                        self.embed = embed
                        self.data = data
                    @discord.ui.button(style=discord.ButtonStyle.red, label=language("delete_button_label").format(cmd=selected_command), custom_id="delete_command")
                    async def delete_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                        button, interaction = interaction, button
                        button.disabled = True
                        for item in self.children:
                            if isinstance(item, discord.ui.Button):
                                item.disabled = True
                        await interaction.edit_original_response(embed=self.embed, view=self)
                        await ctx.reply(language("confirm_deletion").format(cmd=selected_command, ), ephemeral=True)
                        try:
                            user_message = await bot.wait_for(
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
                                await user_message.delete()
                                return
                            elif user_message.content.lower() == "cancel":
                                await user_message.reply(language("deletion_cancelled"))
                                await user_message.delete()
                                return
                            else:
                                await user_message.reply(language("deletion_invalid_command"))
                                await user_message.delete()
                                return
                        except asyncio.TimeoutError:
                            return await ctx.send(language("timeout_message"))
                    @discord.ui.button(style=discord.ButtonStyle.gray, label=language("cancel_button_label"), custom_id="ok")
                    async def ok_button(self, button: discord.ui.Button, interaction: discord.Interaction):
                        button, interaction = interaction, button
                        button.disabled = True
                        for item in self.children:
                            if isinstance(item, discord.ui.Button):
                                item.disabled = True
                        return await interaction.edit_original_response(embed=self.embed, view=self)
                await message.edit(embed=embed, view=ActionSelector(self, selected_command))
            else:
                await ctx.send(language("timeout_message"))
        else:
            await ctx.reply(embed=embed)



#    @commands.hybrid_command(name="permission")
#    @commands.has_permissions(administrator = True)
#    @app_commands.autocomplete(cmd = blackliste_autocompletion)
#    @commands.guild_only()
#    async def permission(self, ctx: Context, member: discord.member):
#        bot = self.bot
#        embed = discord.Embed(title="**Permission du membre:**",description="Permissions accordées au membre.",color=discord.Colour.dark_magenta())
#        commands_list = []
#        data = Botloader.Data.get_user_conf(ctx.guild.id, ctx.author.id, 'cmd')
#        if data and len(data) > 0:
#            data = data.split("\n")
#            for command in data:
#                commands_list.append(command)
#                embed.add_field(name=command, value=Botloader.Data.get_guild_conf(ctx.guild.id, command), inline=False)
#        else:
#            embed.add_field(name="Aucune commande custom disponible pour ce serveur.",value="Créez en avec `/create_command <prefix> <name>`.",inline=False)
#
#        class CommandSelect(Select):
#            def __init__(self, commands):
#                options = [discord.SelectOption(label=cmd, description=f"Select {cmd}") for cmd in commands]
#                super().__init__(placeholder="Sélectionnez une commande", min_values=1, max_values=1, options=options)
#                self.selected_command = None
#            async def callback(self, interaction: discord.Interaction):
#                self.selected_command = self.values[0]
#                self.view.stop()
#        class CommandSelectView(View):
#            def __init__(self, commands, timeout=60):
#                super().__init__(timeout=timeout)
#                self.command_select = CommandSelect(commands)
#                self.add_item(self.command_select)
#            async def on_timeout(self):
#                for item in self.children:
#                    item.disabled = True
#                await self.message.edit(view=self)
#        if commands_list:
#            view = CommandSelectView(commands_list)
#            message = view.message = await ctx.reply(embed=embed, view=view)
#            await view.wait()