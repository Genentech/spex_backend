

class Task:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.content = kwargs.get('content', '')
        self.omeroId = kwargs.get('omeroId', '')
        self.author = kwargs.get('author', '')
        self.parent = kwargs.get('parent', '')
        self.status = kwargs.get('status', 0)
        self.id = kwargs.get('_key', '')
        self._id = kwargs.get('_id', '')
        self.csvdata = kwargs.get('csvdata', [])
        self.impath = kwargs.get('impath', '')

    def to_json(self):
        return {
                'omeroId': self.omeroId,
                'name': self.name,
                'content': self.content,
                'author': self.author,
                'parent': self.parent,
                'status': self.status,
                'csvdata': self.csvdata,
                'id': self.id,
                '_id': self._id,
                'impath': self.impath
                 }


def task(data):
    return Task(**data)
