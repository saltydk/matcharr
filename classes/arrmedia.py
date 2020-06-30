class ArrMedia:
    def __init__(self, title, path, mediaid, slug):
        self.title = title
        self.path = path
        self.id = mediaid
        self.slug = slug

    def to_dict(self):
        return {
            'path': self.path,
            'slug': self.slug,
        }
