# launcher.py
import os
import json
from bot_runner import launch_bot
from updater_runner import run_updater

BOTS = ["", "BetaBelouga", "Belouga", "GameHub"]

# === Charger les chaînes de langue ===
def load_language():
    try:
        with open(".conf", "r") as f:
            config = {k.strip(): v.strip().strip('"') for k, v in 
                      (line.split("=", 1) for line in f if "=" in line and not line.startswith("#"))}
        lang_file = os.path.join("languages", f"{config['language']}_interface")
        with open(lang_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Chargement langue: {e}")
        exit()

STRINGS = load_language()

# === LICENSE ===
LICENSE = open("LICENSE", encoding="utf-8").read()

# === Menu principal ===
def show_menu():
    print("\n=== Launcher ===")
    print("[1] Lancer un bot")
    print("[2] Terminal")
    print("[3] Licence")
    print("[4] Update")
    return input("\nVotre choix: ")

def main():
    choice = show_menu()
    if choice == "1":
        print("Choix du bot:")
        for i, bot in enumerate(BOTS):
            if bot: print(f"[{i}] {bot}")
        bot_id = input("Bot=> ")
        password = input(STRINGS["password_prompt"])
        launch_bot(BOTS[int(bot_id)], password)

    elif choice == "2":
        cmd = input("Commande shell: ")
        os.system(cmd)

    elif choice == "3":
        print(LICENSE)

    elif choice == "4":
        option = input("[1] Check&Update\n[2] Force Update\n")
        run_updater(force=(option == "2"))

if __name__ == "__main__":
    main()
