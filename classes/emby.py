import os


class Emby:
    def __init__(self, path, agent, metadataid, title):
        if os.path.isfile(path):
            self.path = os.path.dirname(os.path.abspath(path))
        else:
            self.path = path
        self.id = agent
        self.metadataid = metadataid
        self.title = title

    def to_dict(self):
        return {
            'title': self.title,
            'id': self.id,
            'metadataid': self.metadataid,
        }