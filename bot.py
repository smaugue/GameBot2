# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import discord
from discord.ext import commands
import os
import argparse

from Packs.version import BOT_VERSION, BOT_VERSION_DATE
from Packs.Botloader import Bot

import time
import functools
#from Packs.Botloader import Bot

def measure_boot_time(func):
    """
    Décorateur pour mesurer le temps de boot du bot.
    Affiche le temps écoulé entre le début et la fin de la fonction décorée.
    """
    @functools.wraps(func)
    async def boot(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = end - start
        Bot.console("INFO", f"Temps de boot : {elapsed:.2f} secondes")
        return result
    return boot


def main():
    parser = argparse.ArgumentParser(description='Script Bot V1.2')
    parser.add_argument('Botname', type=str, default="Bot", help='Nom du bot à lancer')
    parser.add_argument('--pasword', type=str, default="", help="Mot de passe")
    args = parser.parse_args()
    Bot(args.Botname, str(args.pasword))

if __name__ == '__main__':
    main()


class BotClient(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @measure_boot_time
    async def on_ready(self):
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game("Chargement des cookies!")
        )
        Bot.console("INFO", f'Logged in V{BOT_VERSION} ({BOT_VERSION_DATE})')

        # Chargement des Cogs
        for filename in os.listdir("./Cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"Cogs.{filename[:-3]}")
                    Bot.console("INFO", f"Cog {filename} chargé.")
                except Exception as e:
                    Bot.console("WARN", f"Erreur lors du chargement du cog {filename}: {e}")

        Bot.console("INFO", f'Logged in as {self.user} (ID: {self.user.id})')

        try:
            synced = await self.tree.sync()
            Bot.console("INFO", f'Synced {len(synced)} slash commands')
        except Exception as e:
            Bot.console("ERROR", f'Error syncing slash commands: {e}')

        Bot.console("INFO", "Bot is ready.")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name="cookie you!")
        )


# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = BotClient(command_prefix=Bot.Prefix, intents=intents, description="Belouga.exe is watching you!!!")
bot.remove_command('help')

try:
    bot.run(Bot.Token)
except:
    print("Bad Password")
os.system(f"python Launcher.py --bot {Bot.Name} --restart {Bot.Restart} --pasword {Bot.Pasword} {Bot.Update}")