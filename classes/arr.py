import requests
import json


class Arr:
    def __init__(self, url, apikey, mediatype):
        self.request = requests.get(url="{}/api/{}/?apikey={}".format(url, mediatype, apikey))
        self.data = json.loads(self.request.text)
