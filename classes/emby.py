import posixpath


class Emby:
    def __init__(self, path, mappedpath, agent, metadataid, title):
        self.path = path
        self.mappedpath = mappedpath

        if posixpath.isfile(self.mappedpath):
            self.fullpath = posixpath.dirname(posixpath.abspath(self.mappedpath))
        else:
            self.fullpath = self.mappedpath
        self.id = agent
        self.metadataid = metadataid
        self.title = title

    def to_dict(self):
        return {
            'title': self.title,
            'id': self.id,
            'metadataid': self.metadataid,
        }