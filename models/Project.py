

class Project:
    def __init__(self, **kwargs):
        self.id = kwargs.get('_key', '')
        self.name = kwargs.get('name', '')
        self.description = kwargs.get('description', '')
        self.omeroIds = kwargs.get('omeroIds', [])
        self.taskIds = kwargs.get('taskIds', [])
        self.taskResultIds = kwargs.get('taskResultIds', [])
        self.author = kwargs.get('author', '')

    def to_json(self):
        return {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'author': self.author,
                'omeroIds': self.omeroIds,
                'taskIds': self.taskIds,
                'taskResultIds': self.taskResultIds
                 }


def project(data):
    return Project(**data)
