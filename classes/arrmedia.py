class ArrMedia:
    def __init__(self,title,path,id):
        self.title = title
        self.path = path
        self.id = id

    def to_dict(self):
        return {
            'path': self.path,
        }