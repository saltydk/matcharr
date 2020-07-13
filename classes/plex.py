import re
import os


class Plex:
    def __init__(self, path, mapping, agent, metadataid, title):
        self.path = path
        self.mapping = mapping
        self.agent = agent
        self.id = int(re.search(r'\d+', agent).group())
        if os.path.isfile(str(path[0])):
            self.fullpath = os.path.dirname(os.path.abspath(str(path[0])))
        else:
            self.fullpath = str(path[0])
        self.metadataid = metadataid
        self.title = title

    def to_dict(self):
        return {
            'title': self.title,
            'id': self.id,
            'metadataid': self.metadataid,
        }
