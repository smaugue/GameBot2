# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import requests
import base64
from Packs.Botloader import Reposit

repo_owner = Reposit.repo_owner
repo_name = Reposit.repo_name
file_path = "Version"

def get_version():
    data = open("Version", encoding='utf-8')
    lines = data.readlines()
    for line in lines:
        if "VERSION" in line:
            v, u, p, c = line.split("=")[1].strip().replace('"', '').replace("'", "").split(".")
            return int(v), int(u), int(p), int(c)

v,u,p,c = get_version()

BOT_VERSION = f"{v}.{u}.{p}.{c}"

class Version:

    LASTER_VERSION = ""

    def get_github_data():
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

    def get_github_patch():
        decoded_content = Version.get_github_data()
        date = "-/-/-"
        patch = "Non renseigné..."
        for line in decoded_content.split("\n"):
            if "DATE" in line:
                date = line.split("=")[1].strip().replace('"', '').replace("'", "")
            if "LAST_CHANGE" in line:
                patch = line.split("=")[1].strip().replace('"', '').replace("\\n","\n").replace("\\t","\t")
        return date, patch


    def get_github_version():
        decoded_content = Version.get_github_data()
        for line in decoded_content.split("\n"):
            if "VERSION" in line:
                try:
                    v, u, p, c = line.split("=")[1].strip().replace('"', '').replace("'", "").split(".")
                    return int(v), int(u), int(p), int(c)
                except ValueError:
                    pass

    def cmp(version: str):
        bv, bu, bp, bc = Version.get_github_version()
        Version.LASTER_VERSION = f"{bv}.{bu}.{bp}.{bc}"
        if v < bv or v == bv and u < bu or v == bv and u == bu and p < bp:
            return "o"
        if v > bv or v == bv and u > bu or v == bv and u == bu and p > bp:
            return "b"
        return "j"
    
    def check():
        return Version.cmp(BOT_VERSION)
    
    def get_patch():
        return Version.get_github_patch()