import requests
import json


class Arr:
    def __init__(self, url, apikey, mediatype):
        r = requests.get(url="{}/api/v3/{}/?apikey={}".format(url, mediatype, apikey))
        self.data = json.loads(r.text)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        r2 = requests.get(url="{}/api/v3/rootfolder?apikey={}".format(url, apikey), headers=headers)
        self.paths = json.loads(r2.text)
