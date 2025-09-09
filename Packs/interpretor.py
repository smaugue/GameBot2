import discord
import os
import shlex
import aiofiles
import aiohttp
import re
from datetime import datetime
from abc import ABC, abstractmethod
from Packs.Botloader import Bot, Utilitary
import asyncio

# Répertoire temporaire pour les fichiers
TMP_DIR = "tmp"
os.makedirs(TMP_DIR, exist_ok=True)


# ======== Classes d'Actions Abstraites et Concrètes ========
class Action(ABC):
    @abstractmethod
    async def execute(self, ctx):
        """Exécute l'action."""
        pass

class Start():
    @abstractmethod
    async def execute(self, ctx):
        pass


class SendEmbedAction(Action):
    def __init__(self, title, content, color=discord.Color.blue()):
        self.title = title
        self.content = content
        self.color = color

    async def execute(self, ctx):
        embed = discord.Embed(title=self.title, description=self.content, color=self.color)
        await ctx.send(embed=embed)
        Bot.console("INFO", f"[{ctx.author}({ctx.author.id})] Send Embed: {self.title} [{self.content}]")

    # Pas de lourdes opérations réseau ou fichiers donc très léger

class OsuPlayerData(Action):
    def __init__(self, username):
        self.username = username

    async def execute(self, ctx):
        try:
            data = await Utilitary.get_osu_player_data(self.username)
            if data:
                embed = discord.Embed(title=f"Osu! Player: {data['username']}", color=discord.Color.purple())
                embed.add_field(name="PP", value=data['pp'], inline=True)
                embed.add_field(name="Rank", value=data['rank'], inline=True)
                embed.add_field(name="Country Rank", value=data['country_rank'], inline=True)
                embed.add_field(name="Level", value=data['level'], inline=True)
                embed.set_thumbnail(url=data['avatar_url'])
                await ctx.send(embed=embed)
                Bot.console("INFO", f"[{ctx.author}({ctx.author.id})] Osu! data sent for user: {self.username}")
            else:
                await ctx.send(f"No data found for user: {self.username}")
                Bot.console("WARN", f"[{ctx.author}({ctx.author.id})] No Osu! data for user: {self.username}")
        except Exception as e:
            Bot.console("WARN", f"[{ctx.author}({ctx.author.id})] Error fetching Osu! data for {self.username}: {e}")

class SendMessageAction(Action):
    def __init__(self, content):
        self.content = content

    async def execute(self, ctx):
        await ctx.send(self.content)
        Bot.console("INFO", f"[{ctx.author}({ctx.author.id})] Message sent: {self.content}")


# interpreter.py
class GenerateMP3Action(Action):
    def __init__(self, text, lang="fr"):
        self.text = text
        self.lang = lang

    async def execute(self, ctx):
        try:
            file_path = await Utilitary.maketts(self.text, self.lang)
            await ctx.send(file=discord.File(file_path))
            Bot.console("INFO", f"[{ctx.author}({ctx.author.id})] MP3 generated and sent: {file_path} [{self.text}]")
        except Exception as e:
            Bot.console("WARN", f"[{ctx.author}({ctx.author.id})] Error generating MP3: {e}")
        finally:
            if os.path.exists(file_path):
                await asyncio.to_thread(os.remove, file_path)



class CreateRoleAction(Action):
    def __init__(self, name, color):
        self.name = name
        self.color = discord.Color(int(color, 16))

    async def execute(self, ctx):
        try:
            guild = ctx.guild
            await guild.create_role(name=self.name, color=self.color)
            await ctx.send(f"Role '{self.name}' created with color {self.color}.")
            Bot.console("INFO", f"[{ctx.author}({ctx.author.id})] Role created: {self.name} with color {self.color}")
        except Exception as e:
            Bot.console("WARN", f"[{ctx.author}({ctx.author.id})] Error creating role: {e}")


class SendImageFromURLAction(Action):
    def __init__(self, url):
        self.url = url

    async def execute(self, ctx):
        try:
            # Utilisation de aiohttp de manière efficace avec une session persistante
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    if response.status == 200:
                        data = await response.read()
                        image_path = os.path.join(TMP_DIR, "temp_image.png")
                        # Utilisation de aiofiles pour écrire de manière asynchrone
                        async with aiofiles.open(image_path, 'wb') as f:
                            await f.write(data)
                        await ctx.send(file=discord.File(image_path))
                        Bot.console("INFO", f"[{ctx.author}({ctx.author.id})] Image sent from URL: {self.url}")
                        await asyncio.to_thread(os.remove, image_path)
                    else:
                        await ctx.send("Failed to retrieve image from URL.")
                        Bot.console("WARN", f"[{ctx.author}({ctx.author.id})] Failed to retrieve image: HTTP {response.status}")
        except Exception as e:
            Bot.console("WARN", f"[{ctx.author}({ctx.author.id})] Error in SendImageFromURLAction: {e}")


# ======== Utilitaires ========
def get_unique_filename(base_dir, prefix, extension):
    """Génère un nom de fichier unique pour éviter les écrasements."""
    i = 0
    while True:
        suffix = f"_{i}" if i > 0 else ""
        filename = os.path.join(base_dir, f"{prefix}{suffix}.{extension}")
        if not os.path.exists(filename):
            return filename
        i += 1


def replace_arguments(content, arguments):
    """Remplace $1, $2, ... $n dans le contenu avec les arguments fournis."""
    for i, arg in enumerate(arguments, start=1):
        content = content.replace(f"${i}", arg)
    return content


def process_secondary(content, ctx):
    """
    Traite les actions secondaires imbriquées comme Calc[...] et Copy[...] ainsi que @Mention.
    On utilise ici re.sub pour améliorer la lisibilité.
    """

    def calc_repl(match):
        expr = match.group(1)
        try:
            return str(eval(expr))
        except Exception as e:
            Bot.console("WARN", f"[{ctx.author}({ctx.author.id})] Erreur lors de l'évaluation de {expr}: {e}")
            return expr

    def copy_repl(match):
        text = match.group(1)
        return f'```{text}```'

    # Traitement de Calc[...] et Copy[...]
    content = re.sub(r'Calc\[(.*?)\]', calc_repl, content)
    content = re.sub(r'Copy\[(.*?)\]', copy_repl, content)
    # Traitement de @Mention
    content = content.replace("@Mention", ctx.author.mention)

    return content


# ======== Action Registry ========
class ActionRegistry:
    _actions = {}

    @classmethod
    def register(cls, name, action_cls):
        cls._actions[name] = action_cls

    @classmethod
    def get_action(cls, name):
        return cls._actions.get(name)


# Enregistrement des actions
ActionRegistry.register("Start", Start)
ActionRegistry.register("SendMessage", SendMessageAction)
ActionRegistry.register("GenerateMP3", GenerateMP3Action)
ActionRegistry.register("CreateRole", CreateRoleAction)
ActionRegistry.register("SendImage", SendImageFromURLAction)
ActionRegistry.register("SendEmbed", SendEmbedAction)
ActionRegistry.register("OsuPlayerData", OsuPlayerData)


# ======== Parsing des Actions ========
def parse_actions(ctx, actions: str):
    """Analyse une chaîne d'actions et crée des objets Action."""
    if not actions:
        return []

    try:
        args = shlex.split(ctx.message.content)
        arguments = args[1:]
    except Exception as e:
        Bot.console("ERROR", f"[{ctx.author}({ctx.author.id})] Erreur lors du parsing des arguments: {e}")
        arguments = []

    action_list = []
    action_strs = actions.split("}&") if "}&" in actions else [actions]

    for raw_action in action_strs:
        action_str = raw_action.rstrip("}") + "}"
        match = re.fullmatch(r"(\w+)\{(.*)\}", action_str)
        if match:
            action_name, params = match.groups()
            action_cls = ActionRegistry.get_action(action_name)
            if action_cls:
                try:
                    params = replace_arguments(params, arguments)
                    params = process_secondary(params, ctx)
                    escaped_delimiter = "__ESCAPED_SEMICOLON__"
                    params = params.replace(r'\;', escaped_delimiter)
                    params_split = [p.replace(escaped_delimiter, ';').strip() for p in params.split(";") if p]
                    action = action_cls(*params_split)
                    action_list.append(action)
                except Exception as e:
                    Bot.console("ERROR", f"[{ctx.author}({ctx.author.id})] Erreur lors de la création de l'action {action_name}: {e}")
            else:
                Bot.console("WARN", f"[{ctx.author}({ctx.author.id})] Action inconnue: {action_name}")
        else:
            Bot.console("WARN", f"[{ctx.author}({ctx.author.id})] Format d'action invalide: {raw_action}")

    return action_list
