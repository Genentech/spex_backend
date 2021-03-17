

class Job:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.content = kwargs.get('content', '')
        self.id = kwargs.get('id', [])
        self.author = kwargs.get('author', '')

    def to_json(self):
        return {
                'id': self.id,
                'name': self.name,
                'content': self.content,
                'author': self.author
                 }


def job(data):
    return Job(**data)
