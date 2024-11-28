# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import os
import requests
import base64
import argparse

def main():
    parser = argparse.ArgumentParser(description='Scripte Updater.')
    parser.add_argument('--force', action='store_true', help="Force la mise à jour")
    args = parser.parse_args()

    if args.force:
        print("Mise à jour forcée...")
        Version.update_files()
        print(f"Version {Version.LATEST_VERSION}")

    elif version_tuple:
        Version.update_if_needed()

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

repo_owner = config_vars.get("repo_owner")
repo_name = config_vars.get("repo_name")
branch_name = config_vars.get("branch_name")
token = config_vars.get("git_token")
ignore_files = config_vars.get("ignore_files", "").split(" ")

local_folder = os.path.dirname(os.path.abspath(__file__))

def get_version():
    try:
        with open("Version", encoding='utf-8') as data:
            lines = data.readlines()
            for line in lines:
                if "VERSION" in line:
                    v, u, p, c = line.split("=")[1].strip().replace('"', '').replace("'", "").split(".")
                    return int(v), int(u), int(p), int(c)
    except FileNotFoundError:
        print("Le fichier 'Version' est introuvable.")
        return None

version_tuple = get_version()
if version_tuple:
    v, u, p, c = version_tuple
    BOT_VERSION = f"{v}.{u}.{p}.{c}"

class Version:
    LATEST_VERSION = ""

    @staticmethod
    def get_github_data(file_path):
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}?ref={branch_name}"
        response = requests.get(url)
        if response.status_code == 200:
            content = response.json()
            if isinstance(content, list):
                return content
            return content.get('content', '')
        else:
            print(f"Erreur lors de la récupération des données depuis GitHub : {response.status_code}")
            return None

    @staticmethod
    def get_github_version():
        decoded_content = Version.get_github_data("Version")
        if decoded_content:
            for line in base64.b64decode(decoded_content).decode('utf-8').split("\n"):
                if "VERSION" in line:
                    v, u, p, c = line.split("=")[1].strip().replace('"', '').replace("'", "").split(".")
                    return int(v), int(u), int(p), int(c)
        return None

    @staticmethod
    def cmp():
        github_version = Version.get_github_version()
        if github_version:
            bv, bu, bp, bc = github_version
            Version.LATEST_VERSION = f"{bv}.{bu}.{bp}.{bc}"
            if v < bv or (v == bv and u < bu) or (v == bv and u == bu and p < bp):
                return "older"
            if v > bv or (v == bv and u > bu) or (v == bv and u == bu and p > bp):
                return "newer"
            return "up_to_date"
        else:
            print("Impossible de récupérer la version GitHub.")
            return None

    @staticmethod
    def download_file_from_github(file_info, local_path):
        file_name = file_info['name']
        file_path = file_info['path']
        content = Version.get_github_data(file_path)
        if content:
            try:
                decoded_content = base64.b64decode(content).decode('utf-8')
                local_file_path = os.path.join(local_path, file_name)
                with open(local_file_path, 'w', encoding='utf-8') as local_file:
                    local_file.write(decoded_content)
                print(f"Fichier {file_name} mis à jour.")
            except UnicodeDecodeError:
                print(f"Le fichier {file_name} n'est pas un fichier texte. Ignorer...")
                binary_content = base64.b64decode(content)
                local_file_path = os.path.join(local_path, file_name)
                with open(local_file_path, 'wb') as local_file:
                    local_file.write(binary_content)
                print(f"Fichier binaire {file_name} mis à jour.")

    @staticmethod
    def update_files(repo_path="", local_path=local_folder):
        files = Version.get_github_data(repo_path)
        if files:
            for file_info in files:
                file_name = file_info['name']
                file_type = file_info['type']
                if file_type == "file" and file_name not in ignore_files:
                    Version.download_file_from_github(file_info, local_path)
                elif file_type == "dir":
                    sub_folder_local = os.path.join(local_path, file_name)
                    os.makedirs(sub_folder_local, exist_ok=True)
                    Version.update_files(repo_path=file_info['path'], local_path=sub_folder_local)
        else:
            print(f"Erreur lors de la récupération des fichiers depuis GitHub.")

    @staticmethod
    def update_if_needed():
        result = Version.cmp()
        os.system("cls||clear")
        if result == "older":
            print(f"Version locale ({BOT_VERSION}) plus ancienne que la version GitHub ({Version.LATEST_VERSION}). Mise à jour en cours...")
            Version.update_files()
            print("Mise à jour réussie.")
        elif result == "newer":
            print(f"\nATTENTION : La version locale ({BOT_VERSION}) est plus récente que la version sur GitHub ({Version.LATEST_VERSION}).\n")
            print("Aucune mise à jour effectuée.")
        elif result == "up_to_date":
            print("La version locale est à jour.")
        else:
            print("Aucune action effectuée en raison d'une erreur.")

if __name__ == "__main__":
    main()
