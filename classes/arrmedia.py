class ArrMedia:
    def __init__(self, title, path, mapped_path, mediaid, imdb, slug):
        self.title = title
        self.path = path
        self.mappedpath = mapped_path
        self.id = mediaid
        self.imdb = imdb
        self.slug = slug

    def to_dict(self):
        return {
            'path': self.path,
            'slug': self.slug,
        }
