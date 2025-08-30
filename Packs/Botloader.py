# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

"""
Module Botloader
----------------
Regroupe tous les éléments essentiels

Le module permet de récupérer toutes les variables essentielles au bot ainsi que les données des guildes et des utilisateurs.

Data
-----
`Data`

Bot
----
`Bot`
>>> Bot.Name
>>> Bot.Token
>>> Bot.Prefix
"""

import os
import math
import asyncio
import discord
import inspect
import sqlite3
import pytz
import json
from gtts import gTTS
from datetime import datetime
from collections import deque
from enum import Enum

__path__ = os.path.dirname(os.path.abspath(__file__))
tz = pytz.timezone('Europe/Paris')


class owner_permission:
    owner_id = 592737249481850896

    @staticmethod
    def check(member_id):
        return member_id == owner_permission.owner_id


class Conf:
    config_vars = {}

    with open(".conf", "r", encoding="utf-8") as config_file:
        for line in config_file:
            if line.strip() and not line.startswith("#"):
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                config_vars[key] = value


class Data:
    """
    Data
    ----
    Module Database

    Fonctionnalités
    ----------------
    Pour récupérer une valeur:
    - Guild : `Data.get_guild_conf`
    - Utilisateur de guild : `Data.get_user_conf`

    Pour insérer / modifier:
    - Guild : `Data.set_guild_conf`
    - Utilisateur de guild : `Data.set_user_conf`

    Pour supprimer:
    - Guild : `Data.delete_guild_conf`
    - Utilisateur : `Data.delete_user_conf`

    Tips
    -----
    Pour récupérer plus facilement une clé de Database : `Data.<NOM_DE_CLEF>`

    Exemple
    --------
    >>> Data.CUSTOM_COMMANDS_NAMES
    >>> Data.get_guild_conf(guild_id, Data.AUTOMOD_CHANNEL)
    >>> Data.set_guild_conf(guild_id, Data.AUTOMOD_CHANNEL, value)
    >>> Data.delete_guild_conf(guild_id, Data.AUTOMOD_CHANNEL)
    """

    # dictionnaire de correspondance entre clés et leur nom en base
    key_value = {
        'execute': 'command_execute_permission',
        'custom_commands_names': 'custom_commands_names',
        'sayic': 'command_sayic_permission',
        'say': 'command_say_permission',
        'vtts': 'command_vtts_permission',
        'ftts': 'command_ftts_permission',
        'randome': 'command_rdm_permission',
        'testvoca': 'command_testvoca_permission',
        'dm': 'command_dm_permission',
        'dm_blackliste': 'blackliste_dm_id',
        'automod_channel': 'automod_channel_id',
        'automod_level': 'automod_action_level',
        'vtts_directe_message': 'vtts_directe_message',
        'guild_language': 'guild_language',
        'automod_enable': 'automod_enable_state'
    }

    keys = list(key_value.keys())

    EXECUTE = keys[0]
    CUSTOM_COMMANDS_NAMES = keys[1]
    SAYIC = keys[2]
    SAY = keys[3]
    VTTS = keys[4]
    FTTS = keys[5]
    RANDOM = keys[6]
    TESTVOCA = keys[7]
    DM = keys[8]
    DM_BLACKLISTE = keys[9]
    AUTOMOD_CHANNEL = keys[10]
    AUTOMOD_LEVEL = keys[11]
    VTTS_DIRECTE_MESSAGE = keys[12]
    GUILD_LANGUAGE = keys[13]
    AUTOMOD_ENABLE = keys[14]

    def __init__(self, db_path):
        self.db_path = db_path
        # Création de la base de données et des tables si nécessaires
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            self.create_tables(cursor)
            connection.commit()

    def create_tables(self, cursor):
        cursor.execute('''CREATE TABLE IF NOT EXISTS guild_conf (
                                guild_id INTEGER,
                                conf_key TEXT,
                                conf_value TEXT,
                                PRIMARY KEY (guild_id, conf_key)
                            )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS user_conf (
                                guild_id INTEGER,
                                user_id INTEGER,
                                conf_key TEXT,
                                conf_value TEXT,
                                PRIMARY KEY (guild_id, user_id, conf_key)
                            )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS user_game_data (
                                user_id INTEGER,
                                guild_id INTEGER,
                                game_key TEXT,
                                game_value TEXT,
                                PRIMARY KEY (user_id, guild_id, game_key)
                            )''')

        # Ajout des index pour améliorer les performances des requêtes
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_guild_conf ON guild_conf (guild_id, conf_key)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_user_conf ON user_conf (guild_id, user_id, conf_key)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_user_game_data ON user_game_data (user_id, guild_id, game_key)''')

    @staticmethod
    def _execute(query, params=(), fetchone=False, commit=False):
        # Utilisation de Bot.Name pour construire le nom de la base de données
        with sqlite3.connect(f"{Bot.Name}.db") as connection:
            cursor = connection.cursor()
            cursor.execute(query, params)
            if commit:
                connection.commit()
            if fetchone:
                return cursor.fetchone()
            else:
                return cursor.fetchall()

    @staticmethod
    def set_guild_conf(guild_id, conf_key, conf_value):
        if Data.get_guild_conf(guild_id, conf_key):
            Data._execute('''UPDATE guild_conf
                             SET conf_value = ?
                             WHERE guild_id = ? AND conf_key = ?''',
                          (conf_value, guild_id, conf_key), commit=True)
        else:
            Data._execute('''INSERT OR REPLACE INTO guild_conf (guild_id, conf_key, conf_value)
                             VALUES (?, ?, ?)''',
                          (guild_id, conf_key, conf_value), commit=True)

    @staticmethod
    def set_user_conf(guild_id, user_id, conf_key, conf_value):
        if Data.get_user_conf(guild_id, user_id, conf_key):
            Data._execute('''UPDATE user_conf
                             SET conf_value = ?
                             WHERE guild_id = ? AND user_id = ? AND conf_key = ?''',
                          (conf_value, guild_id, user_id, conf_key), commit=True)
        else:
            Data._execute('''INSERT OR REPLACE INTO user_conf (guild_id, user_id, conf_key, conf_value)
                             VALUES (?, ?, ?, ?)''',
                          (guild_id, user_id, conf_key, conf_value), commit=True)

    @staticmethod
    def set_user_game_data(user_id, guild_id, game_key, game_value):
        if Data.get_user_game_data(user_id, guild_id, game_key):
            Data._execute('''UPDATE user_game_data
                             SET game_value = ?
                             WHERE user_id = ? AND guild_id = ? AND game_key = ?''',
                          (game_value, user_id, guild_id, game_key), commit=True)
        else:
            Data._execute('''INSERT OR REPLACE INTO user_game_data (user_id, guild_id, game_key, game_value)
                             VALUES (?, ?, ?, ?)''',
                          (user_id, guild_id, game_key, game_value), commit=True)

    @staticmethod
    def get_guild_conf(guild_id, conf_key):
        result = Data._execute('''SELECT conf_value FROM guild_conf
                                  WHERE guild_id = ? AND conf_key = ?''',
                               (guild_id, conf_key), fetchone=True)
        return result[0] if result else None

    @staticmethod
    def get_user_conf(guild_id, user_id, conf_key):
        result = Data._execute('''SELECT conf_value FROM user_conf
                                  WHERE guild_id = ? AND user_id = ? AND conf_key = ?''',
                               (guild_id, user_id, conf_key), fetchone=True)
        return result[0] if result else None

    @staticmethod
    def get_user_game_data(user_id, guild_id, game_key):
        result = Data._execute('''SELECT game_value FROM user_game_data
                                  WHERE user_id = ? AND guild_id = ? AND game_key = ?''',
                               (user_id, guild_id, game_key), fetchone=True)
        return result[0] if result else None

    @staticmethod
    def delete_guild_conf(guild_id, conf_key):
        Data._execute('''DELETE FROM guild_conf
                         WHERE guild_id = ? AND conf_key = ?''',
                      (guild_id, conf_key), commit=True)

    @staticmethod
    def delete_user_conf(guild_id, user_id, conf_key):
        Data._execute('''DELETE FROM user_conf
                         WHERE guild_id = ? AND user_id = ? AND conf_key = ?''',
                      (guild_id, user_id, conf_key), commit=True)

    @staticmethod
    def delete_user_game_data(user_id, guild_id, game_key):
        Data._execute('''DELETE FROM user_game_data
                         WHERE user_id = ? AND guild_id = ? AND game_key = ?''',
                      (user_id, guild_id, game_key), commit=True)


class Bot:
    """
    Bot
    ----

    Variables et fonctions essentielles pour le bot.

    Variables
    ----------

    Permet de récupérer des info sur le Bot
    
    `Name` -> str()
    `Token` -> str()
    `BotGuild` -> int()
    `AnnonceChannel` -> int()
    `ConsoleChannel` -> int()
    `MessageChannel` -> int()
    `BugReportChannel` -> int()
    `Prefix` -> str()
    `Pasword` -> str()

    Fonctions
    ----------

    >>> `console` -> (voir Bot.console)
    >>> `maketts(text, langage, name = "output.mp3")` -> Retourne le nom d'un mp3 du texte fournit dans la langue fournit

    """

    def __init__(self, launched_bot, pasword):
        Bot.start_time = datetime.now(tz).strftime('%Y-%m-%d_%H:%M:%S')
        Bot.Pasword = pasword
        Bot.Name = Conf.config_vars.get(f"{launched_bot}_name")
        Bot.Token = self.get_token(Conf.config_vars.get(f"{launched_bot}_token"))
        Bot.BotGuild = Conf.config_vars.get(f"{launched_bot}_guild")
        Bot.AnnonceChannel = Conf.config_vars.get(f"{launched_bot}_annonce_channel")
        Bot.ConsoleChannel = Conf.config_vars.get(f"{launched_bot}_console_channel")
        Bot.MessageChannel = Conf.config_vars.get(f"{launched_bot}_message_channel")
        Bot.BugReportChannel = Conf.config_vars.get(f"{launched_bot}_bugreport_channel")
        Bot.Prefix = Conf.config_vars.get(f"{launched_bot}_prefix")
        Bot.Database = Data(f"{Bot.Name}.db")
    
    def get_token(self, token):
        # Optimisation de la décryption du token avec une compréhension de liste
        codes = token.split()
        return "".join(chr((int(code) - ord(self.Pasword[i % len(self.Pasword)])) % 256)
                       for i, code in enumerate(codes))
        
    @staticmethod
    def logs(data):
        try:
            now = datetime.now(tz)
            startDate = now.strftime('%Y-%m-%d')
            with open(f"logs/{startDate}.log", "a+", encoding="utf-8") as logs_file:
                logs_file.write(data + "\n")
        except Exception as e:
            Bot.console("ERROR", f"Log impossible: {e}", False)

    @staticmethod
    async def on_refus_interaction(ctx, *arg):
        language = Bot.get_language(Data.get_guild_conf(ctx.guild.id, Data.GUILD_LANGUAGE))
        await ctx.reply(language("error_insufficient_permissions"), ephemeral=True)

    @staticmethod
    def console(type, arg, log: bool = True):
        """
        Utilisation:
        ------------
        `type`: type de log (info, warn, error, debug)
        `arg`: se qui doit être print

        Exemple:
        --------
        >>> console("INFO", "Bot loggin")
        """
        colors = {
            "INFO": "\033[94m",    # Blue
            "WARN": "\033[93m",    # Yellow
            "ERROR": "\033[91m",   # Red
            "DEBUG": "\033[92m",   # Green
            "FUNCTION": "\033[35m",# Violet
            "GRAY": "\033[90m",    # Gray
            "ENDC": "\033[0m"      # Reset color
        }
        now = datetime.now(tz)
        startDate = now.strftime('%Y-%m-%d')
        startTime = now.strftime('%H:%M:%S')
        color = colors.get(type.upper(), colors["ENDC"])
        if log:
            data = f"{startDate} {startTime} {type}\t{inspect.stack()[1].function}: {arg}"
            Bot.logs(data)
        print(f"{colors['GRAY']}{startDate} {startTime} {color}{type}{colors['ENDC']}\t{colors['FUNCTION']}{inspect.stack()[1].function}{colors['ENDC']}: {arg}")

    @staticmethod
    def get_language(language: str = None):
        language = language or "en"
        """
        Charge un fichier de langue et retourne une fonction utilitaire pour obtenir des chaînes de traduction.
        
        :param language: Code de la langue (par défaut : "en").
        :return: Une fonction utilitaire pour récupérer des chaînes traduites.
        """
        lang_file_path = os.path.join("languages", language)
    
        try:
            with open(lang_file_path, "r", encoding="utf-8") as lang_file:
                STRINGS = json.load(lang_file)
        except FileNotFoundError:
            raise ValueError(f"Language file for '{language}' not found.")
    
        def translate(key: str, **kwargs):
            try:
                template = STRINGS[key]
                return template.format(**kwargs) if kwargs else template
            except KeyError:
                Bot.console("ERROR", f"[Translation Missing: {key}]")
                return f"[Translation Missing: {key}]"
            except Exception as e:
                Bot.console("ERROR", f"[Error in Translation: {e}]")
                return f"[Error in Translation: {e}]"
    
        return translate
    

class Reposit:
    repo_owner = Conf.config_vars.get("repo_owner")
    repo_name = Conf.config_vars.get("repo_name")
    token = Conf.config_vars.get("git_token")

class YTDV3:
    api_key = Conf.config_vars.get("youtube_api_key")


TMP_DIR = "tmp"

def get_unique_filename(directory, base_name, extension):
    """Retourne un chemin unique pour un fichier dans un dossier donné."""
    counter = 0
    while True:
        filename = f"{base_name}{'' if counter == 0 else f'_{counter}'}.{extension}"
        filepath = os.path.join(directory, filename)
        if not os.path.exists(filepath):
            return filepath
        counter += 1


class Utilitary:

    @staticmethod
    async def maketts(text: str, language: str = "fr", name: str | None = None) -> str:
        """
        Génère un fichier TTS en mp3 et retourne son chemin.
        Si name est None → génère un nom unique basé sur timestamp et user.
        """
        os.makedirs(TMP_DIR, exist_ok=True)
        if name:
            file_path = os.path.join(TMP_DIR, name)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = get_unique_filename(TMP_DIR, f"tts_{timestamp}", "mp3")

        tts_instance = gTTS(text, lang=language)
        await asyncio.to_thread(tts_instance.save, file_path)
        return file_path
    
    
    queue = deque()

    @staticmethod
    async def play_audio(ctx, file):
        if ctx.voice_client.is_playing():
            Utilitary.queue.append((ctx, file))
            await ctx.reply("Audio ajouté à la file d'attente.", ephemeral=True)
        else:
            ctx.voice_client.play(discord.FFmpegPCMAudio(file),
                                  after=lambda e: Utilitary.on_play_finish(ctx, file))

    @staticmethod
    def on_play_finish(ctx, file):
        try:
            os.remove(file)
        except Exception as e:
            Bot.console("ERROR", f"Erreur lors de la suppression du fichier audio: {e}")
        if Utilitary.queue:
            next_ctx, next_file = Utilitary.queue.popleft()
            asyncio.run_coroutine_threadsafe(Utilitary.play_audio(next_ctx, next_file), ctx.bot.loop)
