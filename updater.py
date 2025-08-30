# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import os
import requests
import base64
import argparse
from fnmatch import fnmatch

# === Chargement de la config (.conf + .gitignore) ===

def load_conf():
    config_vars = {}
    with open(".conf", "r", encoding="utf-8") as config_file:
        for line in config_file:
            if line.strip() and not line.startswith("#"):
                key, value = line.split("=", 1)
                key, value = key.strip(), value.strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                config_vars[key] = value
    return config_vars

def load_gitignore():
    ignore_patterns = []
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ignore_patterns.append(line)
    return ignore_patterns

config_vars = load_conf()
ignore_patterns = load_gitignore()

repo_owner = config_vars.get("repo_owner")
repo_name = config_vars.get("repo_name")
branch_name = config_vars.get("branch_name")
token = config_vars.get("git_token")

local_folder = os.path.dirname(os.path.abspath(__file__))


# === Gestion des versions ===

def get_local_version():
    try:
        with open("Version", encoding='utf-8') as f:
            for line in f:
                if "VERSION = " in line:
                    return tuple(map(int, line.split("=")[1].strip().replace('"', '').replace("'", "").split(".")))
    except FileNotFoundError:
        print("⚠️ Fichier 'Version' introuvable.")
    return None

local_version = get_local_version()
BOT_VERSION = ".".join(map(str, local_version)) if local_version else "0.0.0.0"


# === Classe Version ===

class Version:
    LATEST_VERSION = "?"

    @staticmethod
    def get_github_data(file_path):
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}?ref={branch_name}"
        headers = {"Authorization": f"token {token}"} if token else {}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            content = response.json()
            return content if isinstance(content, list) else content.get("content", "")
        print(f"❌ Erreur GitHub {response.status_code} pour {file_path}")
        return None

    @staticmethod
    def get_github_version():
        decoded_content = Version.get_github_data("Version")
        if decoded_content:
            try:
                text = base64.b64decode(decoded_content).decode("utf-8")
                for line in text.splitlines():
                    if "VERSION" in line:
                        v = tuple(map(int, line.split("=")[1].strip().replace('"', '').replace("'", "").split(".")))
                        return v
            except Exception as e:
                print(f"⚠️ Impossible de lire la version GitHub : {e}")
        return None

    @staticmethod
    def cmp():
        github_version = Version.get_github_version()
        if not (local_version and github_version):
            return None

        Version.LATEST_VERSION = ".".join(map(str, github_version))

        if local_version < github_version:
            return "older"
        if local_version > github_version:
            return "newer"
        return "up_to_date"

    @staticmethod
    def is_ignored(file_path):
        """Vérifie si un fichier correspond à un pattern du .gitignore ou de la conf"""
        for pattern in ignore_patterns + config_vars.get("ignore_files", "").split():
            if fnmatch(file_path, pattern) or fnmatch(os.path.basename(file_path), pattern):
                return True
        return False

    @staticmethod
    def download_file_from_github(file_info, local_path):
        file_name = file_info["name"]
        file_path = file_info["path"]

        if Version.is_ignored(file_name) or Version.is_ignored(file_path):
            print(f"⏭️ Ignoré : {file_path}")
            return

        content = Version.get_github_data(file_path)
        if content:
            try:
                decoded_content = base64.b64decode(content).decode("utf-8")
                with open(os.path.join(local_path, file_name), "w", encoding="utf-8") as f:
                    f.write(decoded_content)
                print(f"✅ {file_name} mis à jour")
            except UnicodeDecodeError:
                binary_content = base64.b64decode(content)
                with open(os.path.join(local_path, file_name), "wb") as f:
                    f.write(binary_content)
                print(f"📦 {file_name} (binaire) mis à jour")

    @staticmethod
    def update_files(repo_path="", local_path=local_folder):
        files = Version.get_github_data(repo_path)
        if not files:
            print("❌ Impossible de récupérer les fichiers GitHub")
            return

        for file_info in files:
            file_name, file_type = file_info["name"], file_info["type"]
            if file_type == "file":
                Version.download_file_from_github(file_info, local_path)
            elif file_type == "dir":
                sub_folder = os.path.join(local_path, file_name)
                os.makedirs(sub_folder, exist_ok=True)
                Version.update_files(repo_path=file_info["path"], local_path=sub_folder)

    @staticmethod
    def update_if_needed():
        result = Version.cmp()
        os.system("cls||clear")

        if result == "older":
            print(f"⬇️ Mise à jour de {BOT_VERSION} → {Version.LATEST_VERSION}")
            Version.update_files()
            print("✅ Mise à jour terminée.")
        elif result == "newer":
            print(f"⚠️ Version locale ({BOT_VERSION}) plus récente que GitHub ({Version.LATEST_VERSION})")
        elif result == "up_to_date":
            print(f"✔️ Déjà à jour ({BOT_VERSION})")
        else:
            print("❌ Erreur lors de la vérification des versions.")


# === Main ===

def main():
    parser = argparse.ArgumentParser(description="Script Updater")
    parser.add_argument("--force", action="store_true", help="Forcer la mise à jour")
    args = parser.parse_args()

    if args.force:
        print("⚡ Mise à jour forcée...")
        Version.update_files()
    else:
        Version.update_if_needed()

if __name__ == "__main__":
    main()
