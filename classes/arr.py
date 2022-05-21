import requests
import json


class Arr:
    def __init__(self, url, apikey, mediatype):
        r = requests.get(url=f"{url}/api/v3/{mediatype}/?apikey={apikey}")
        self.data = json.loads(r.text)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        r2 = requests.get(url=f"{url}/api/v3/rootfolder?apikey={apikey}", headers=headers)
        self.paths = json.loads(r2.text)
