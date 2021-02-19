

class Image:
    def __init__(self, **kwargs):
        self.id = kwargs.get('_key', None)
        self.path = kwargs.get('path', '')
        self.omeroId = kwargs.get('omeroId', '')

    def to_json(self):
        return {
            'id': self.id,
            'path': self.path,
            'omeroId': self.omeroId,
        }


def image(data):
    return Image(**data)
