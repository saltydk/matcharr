class ArrMedia:
    def __init__(self,title,path,id,slug):
        self.title = title
        self.path = path
        self.id = id
        self.slug = slug

    def to_dict(self):
        return {
            'path': self.path,
            'slug': self.slug,
        }