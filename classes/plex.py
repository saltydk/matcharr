import re


class Plex:
    def __init__(self, path, root, agent, metadataid, title):
        self.path = path
        self.root = root
        self.agent = agent
        self.id = int(re.search(r'\d+', agent).group())
        self.fullpath = "{}/{}".format(root, path)
        self.metadataid = metadataid
        self.title = title

    def to_dict(self):
        return {
            'title': self.title,
            'id': self.id,
            'metadataid': self.metadataid,
        }
