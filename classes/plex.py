import posixpath
import re


class Plex:
    def __init__(self, path, agent, metadataid, title):
        self.agent = "unknown"
        self.id = 0

        if agent.startswith("com.plexapp.agents.themoviedb"):
            self.agent = "themoviedb"
            self.id = int(re.search(r'\d+', agent).group())

        elif agent.startswith("com.plexapp.agents.thetvdb"):
            self.agent = "thetvdb"
            self.id = int(re.search(r'\d+', agent).group())

        elif agent.startswith("com.plexapp.agents.imdb"):
            self.agent = "imdb"
            self.id = re.search(r'(tt[0-9]{7,})', agent).group()

        if posixpath.isfile(path):
            self.fullpath = posixpath.dirname(posixpath.abspath(path))
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
