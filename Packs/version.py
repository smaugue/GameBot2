# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import requests
import base64
from Packs.Botloader import Reposit

repo_owner = Reposit.repo_owner
repo_name = Reposit.repo_name
file_path = "Version"

def get_local_version():
    with open(file_path, encoding='utf-8') as data:
        lines = data.readlines()
    for line in lines:
        if line.strip().startswith("VERSION"):
            v, u, p, c = line.split("=")[1].strip().replace('"', '').replace("'", "").split(".")
            return int(v), int(u), int(p), int(c)
    raise ValueError("Impossible de lire VERSION dans le fichier local.")

v, u, p, c = get_local_version()
BOT_VERSION = f"{v}.{u}.{p}.{c}"

class Version:
    LASTER_VERSION = ""

    @staticmethod
    def get_github_data():
        """Récupère le contenu brut du fichier Version sur GitHub"""
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
        response = requests.get(url)
        if response.status_code == 200:
            content = response.json().get('content', '')
            if content:
                decoded_content = base64.b64decode(content).decode('utf-8')
                return decoded_content
        else:
            response.raise_for_status()
        return None

    @staticmethod
    def get_github_patch():
        """Récupère DATE et LAST_CHANGE du repo GitHub"""
        decoded_content = Version.get_github_data()
        date = "-/-/-"
        last_change = "Non renseigné..."
        for line in decoded_content.split("\n"):
            if line.strip().startswith("DATE"):
                date = line.split("=")[1].strip().replace('"', '').replace("'", "")
            if line.strip().startswith("LAST_CHANGE"):
                # récupérer les lignes multi-texte entre guillemets
                last_change = line.split("=", 1)[1].strip()
                last_change = last_change.strip('"').strip("'")
                # gestion des \n
                last_change = last_change.replace("\\n", "\n").replace("\\t", "\t")
        return date, last_change

    @staticmethod
    def get_github_version():
        """Lit la VERSION du fichier GitHub"""
        decoded_content = Version.get_github_data()
        for line in decoded_content.split("\n"):
            if line.strip().startswith("VERSION"):
                v, u, p, c = line.split("=")[1].strip().replace('"', '').replace("'", "").split(".")
                return int(v), int(u), int(p), int(c)
        raise ValueError("Impossible de lire VERSION depuis GitHub.")

    @staticmethod
    def cmp(version: str):
        """Compare version locale et distante.
        Retourne :
        - 'o' → une version plus récente est en ligne
        - 'b' → la version locale est plus avancée (rare, test/dev)
        - 'j' → les versions correspondent
        """
        bv, bu, bp, bc = Version.get_github_version()
        Version.LASTER_VERSION = f"{bv}.{bu}.{bp}.{bc}"
        if v < bv or (v == bv and u < bu) or (v == bv and u == bu and p < bp):
            return "o"
        if v > bv or (v == bv and u > bu) or (v == bv and u == bu and p > bp):
            return "b"
        return "j"

    @staticmethod
    def check():
        return Version.cmp(BOT_VERSION)

    @staticmethod
    def get_patch():
        return Version.get_github_patch()
