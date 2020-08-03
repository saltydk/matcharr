import posixpath
import re


class Plex:
    def __init__(self, path, mappedpath, agent, metadataid, title):
        self.agent = "unknown"
        self.id = 0
        self.path = path

        if agent.startswith("com.plexapp.agents.themoviedb"):
            self.agent = "themoviedb"
            self.id = int(re.search(r'\d+', agent).group())

        elif agent.startswith("com.plexapp.agents.thetvdb"):
            self.agent = "thetvdb"
            self.id = int(re.search(r'\d+', agent).group())

        elif agent.startswith("com.plexapp.agents.imdb"):
            self.agent = "imdb"
            self.id = re.search(r'(tt[0-9]{7,})', agent).group()

        if posixpath.isfile(mappedpath):
            self.mappedpath = posixpath.dirname(posixpath.abspath(mappedpath))
        else:
            self.mappedpath = mappedpath
        self.metadataid = metadataid
        self.title = title

    def to_dict(self):
        return {
            'title': self.title,
            'id': self.id,
            'metadataid': self.metadataid,
        }
