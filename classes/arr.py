import requests
import json

class Arr:
    def __init__(self,url,apikey,type):
        self.request = requests.get(url="{}/api/{}/?apikey={}".format(url,type,apikey))
        self.data = json.loads(self.request.text)