

class Image:
    def __init__(self, **kwargs):
        self.id = kwargs.get('_key', None)
        self.name = kwargs.get('name', '')
        self.omeroId = kwargs.get('omeroId', '')
        self.paths = kwargs.get('paths', [])

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'omeroId': self.omeroId,
            'paths': self.paths,
        }


def image(data):
    return Image(**data)
