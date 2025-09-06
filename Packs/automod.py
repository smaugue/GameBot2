# Ce projet est sous licence CC BY-NC-SA 4.0
# Voir : https://creativecommons.org/licenses/by-nc-sa/4.0/

import requests
from Packs.Botloader import Bot, Conf
from requests.exceptions import ConnectionError, Timeout

class AutoMod:
    """
    API Automod
    -----------
    API pour l'auto-modération

    ENDPOINTS
    --------
    >>> `/check_message` -> "black_word":{"message_word":"true_word"}, "black_word_similarity":{"message_word":"similarity"}, "version":"x.x.x"
    >>> `/version` -> "version":"x.x.x"

    FONCTIONS
    ---------

    >>> `check_message(message)` -> bw={"message_word":"true_word"}, bws={"message_word":"similarity"}
    >>> `version()` -> v="version format x.x.x"

    Exemple
    -------
    >>> bw, bws = check_message(message)
    >>> for key in blw:
    >>>     print(f"Mot {key} détecté: {round(blws[key], 2) * 100}% de ressemblance avec {blw[key]}.")
    """
    API_KEY = Conf.config_vars.get("api_key")
    API_URL = Conf.config_vars.get("api_url")
    API_PORT = Conf.config_vars.get("api_port")

    url = f"http://{API_URL}:{API_PORT}"
    
    def check_message(message: str,*,level = 3):
        bw = {}
        bws = {}
        api_url = f'{AutoMod.url}/check_message'
        data = {'level':level,'message': message}
        headers = {'x-api-key': AutoMod.API_KEY}
        try:
            response = requests.post(api_url, json=data, headers=headers, timeout=1)
            response.raise_for_status()  # Raise an exception for HTTP errors
        except (ConnectionError, Timeout) as e:
            Bot.console("ERROR", f"Connection error: {e}")
            return bw, bws
        except requests.HTTPError as e:
            Bot.console("ERROR", f"HTTP error: {e.response.status_code}: {e.response.text}")
            return bw, bws

        response_data = response.json()
        bw = response_data.get('black_word')
        bws = response_data.get('black_word_similarity')
        return bw, bws

    def automod_version():
        api_url = f'{AutoMod.url}/version'
        headers = {'x-api-key': AutoMod.API_KEY}
        try:
            response = requests.post(api_url, headers=headers, timeout=5)
            response.raise_for_status()
        except (ConnectionError, Timeout) as e:
            Bot.console("ERROR", f"Connection error: {e}")
            return 'x.x.x'
        except requests.HTTPError as e:
            Bot.console("ERROR", f"HTTP error: {e.response.status_code}: {e.response.text}")
            return 'x.x.x'

        response_data = response.json()
        return response_data.get('version', 'unknown')

    def handcheck():
        api_url = f'{AutoMod.url}/handcheck'
        headers = {'x-api-key': AutoMod.API_KEY}
        try:
            response = requests.post(api_url, headers=headers, timeout=5)
            response.raise_for_status()
        except (ConnectionError, Timeout) as e:
            Bot.console("ERROR", f"Connection error: {e}")
            return False, "x.x.x"
        except requests.HTTPError as e:
            Bot.console("ERROR", f"HTTP error: {e.response.status_code}: {e.response.text}")
            return False, "x.x.x"
        except Exception as e:
            Bot.console("ERROR", f"Unexpected error: {e}")
            return False, "x.x.x"

        response_data = response.json()
        version = response_data.get('version', "x.x.x")
        return True, version