# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import os
import json
import argparse
import subprocess

def load_language():
    """Charge les chaînes en fonction de la langue définie dans le fichier .conf"""
    try:
        config_vars = {}
        with open(".conf", "r") as config_file:
            for line in config_file:
                if line.strip() and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    config_vars[key] = value
        language = config_vars["language"]
        lang_file_path = os.path.join("languages", f"{language}_interface")

        with open(lang_file_path, "r", encoding="utf-8") as lang_file:
            return json.load(lang_file)
    except Exception as e:
        print(f"Erreur lors du chargement des fichiers de langue : {e}")
        exit()

# Charger les chaînes de texte en fonction de la langue
STRINGS = load_language()

def main():
    try:
        parser = argparse.ArgumentParser(description='Scripte Launcher.')
        parser.add_argument('--bot', type=str, default="Bot", help=STRINGS["bot_choice"])
        parser.add_argument('--restart', type=str, default="n", help='Redémarrage du bot (y/n).')
        parser.add_argument('--pasword', type=str, default="pasword", help=STRINGS["password_prompt"])
        parser.add_argument('--update', action='store_true', help=STRINGS["update_choice"])
        args = parser.parse_args()

        if args.update:
            if args.restart.lower() == "y":
                with open("temp_args", "w") as temp_file:
                    temp_file.write(f"{args.bot},{args.pasword}")
            run_updater()

        if args.restart.lower() == "y":
            launch_bot(args.bot, args.pasword)

        else:
            try:
                with open("temp_args", "r") as temp_file:
                    ligne = temp_file.readline()
                if ligne != "":
                    bot, pasword = ligne.split(",")
                    os.remove("temp_args")
                    launch_bot(bot, pasword)
            except FileNotFoundError:
                start()

    except SystemExit as e:
        print(f"{STRINGS['error']} {e}")
        raise

LICENCE = open("LICENCE").read()

def force_run_updater():
    print(LICENCE)
    print(STRINGS["update_choice"])
    try:
        subprocess.run(["python", "updater.py", "--force"], check=True)
        subprocess.run(["python", "Launcher.py"], check=True)
    except Exception as e:
        print(f"{STRINGS['error']} {e}")
    exit()

def run_updater():
    print(LICENCE)
    print(STRINGS["update_choice"])
    try:
        subprocess.run(["python", "updater.py"], check=True)
        subprocess.run(["python", "Launcher.py"], check=True)
    except Exception as e:
        print(f"{STRINGS['error']} {e}")
    exit()

liste = ["", "BetaBelouga", "Belouga", "GameHub"]

def start():
    choice = input(f"""
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
@    _________________________________________________________________________________________________________________    @
@                                                                                                                         @
@    #####  ###### #      ###### #    # ######      #      #          #     #    # #    # ###### #    # ###### #####      @
@    #    # #      #      #    # #    # #    #     # #     #         # #    #    # # #  # #      #    # #      #    #     @
@    #####  ####   #      #    # #    # #         #   #    #        #   #   #    # #  # # #      ###### ####   #####      @
@    #    # #      #      #    # #    # #   ###  #######   #       #######  #    # #   ## #      #    # #      #    #     @
@    #####  #####  ###### ###### ###### ######  #       #  ###### #       # ###### #    # ###### #    # ###### #     #    @
@    _________________________________________________________________________________________________________________    @
@                                                                                             By Smaugue#9833             @
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
{STRINGS['welcome']}
{STRINGS['choose_option']}
[1]{STRINGS['bot_choice']}
[2]Terminal
[3]Licence
[4]{STRINGS['update_choice']}
""")
    if not choice.isdigit():
        print(STRINGS["invalid_input"])
        start()
    if choice == "4":
        option = input("""
[1]Check&Update
[2]Force Update
""")
        if not option.isdigit():
            print(STRINGS["invalid_input"])
            start()
        if option == "1":
            run_updater()
        if option == "2":
            force_run_updater()
        else: start()
    if choice == "3":
        print(LICENCE)
        start()
    if choice == "2":
        commande = input("launcher:")
        try:
            os.system(commande)
        except Exception as e:
            print(e)
        start()
    if choice == "1":
        bot = input(f"""
=========================================================
|    {STRINGS['bot_choice']}                            |
|    {STRINGS['bot_list']}                              |
|    _____________________________                      |
|   |[versions]|[___Bot___]|[code]|                     |
|   |     x    |BetaBelouga|   1  |                     |
|   |     x    |  Belouga  |   2  |                     |
|   |     x    |  GameHub  |   3  |                     |
|   '''''''''''''''''''''''''''''''                     |
=========================================================

Bot=>   """)
        if not bot.isdigit():
            print(STRINGS["invalid_input"])
            start()

        pasword = input(STRINGS["password_prompt"])

        try:
            launch_bot(bot_name = liste[int(bot)], pasword=pasword)
        except Exception as errors:
            print(f"{STRINGS['error']} {errors}")
            start()
    else: start()

def launch_bot(bot_name, pasword):
    try:
        os.system(f"python bot.py {bot_name} --pasword {pasword}")
    except Exception as errors:
        print(f"{STRINGS['error']} {errors}")
        start()

if __name__ == '__main__':
    main()
