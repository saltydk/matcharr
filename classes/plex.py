import re
import os


class Plex:
    def __init__(self, path, agent, metadataid, title):
        self.path = path
        self.agent = agent
        self.id = int(re.search(r'\d+', agent).group())
        if os.path.isfile(path):
            self.fullpath = os.path.dirname(os.path.abspath(path))
        else:
            self.fullpath = path
        self.metadataid = metadataid
        self.title = title

    def to_dict(self):
        return {
            'title': self.title,
            'id': self.id,
            'metadataid': self.metadataid,
        }
