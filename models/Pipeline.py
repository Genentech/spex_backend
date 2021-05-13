

class Pipeline:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.author = kwargs.get('author', '')
        self._from = kwargs.get('_from', '')
        self._to = kwargs.get('_to', '')
        self.startnext = kwargs.get('startnext', 0)
        self.pipeline = kwargs.get('pipeline', '')
        self.id = kwargs.get('_key', '')
        self._id = kwargs.get('_id', '')

    def to_json(self):
        return {
                'name': self.name,
                'author': self.author,
                '_from': self._from,
                '_to': self._to,
                'startnext': self.startnext,
                'id': self.id,
                '_id': self._id,
                'pipeline': self.pipeline
                 }


def pipeline(data):
    return Pipeline(**data)
