

class Project:
    def __init__(self, **kwargs):
        self.id = kwargs.get('_key', '')
        self.name = kwargs.get('name', '')
        self.description = kwargs.get('description', '')
        self.omeroIds = kwargs.get('omeroIds', [])
        self.taskIds = kwargs.get('taskIds', [])
        self.resource_ids = kwargs.get('resource_ids', [])
        self.author = kwargs.get('author', '')

    def to_json(self):
        return {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'author': self.author,
                'omeroIds': self.omeroIds,
                'taskIds': self.taskIds,
                'resource_ids': self.resource_ids
                 }


def project(data):
    return Project(**data)
