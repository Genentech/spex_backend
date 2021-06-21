

class Connection:
    def __init__(self, **kwargs):
        self.id = kwargs.get('_key', '')
        self._id = kwargs.get('_id', '')
        self._from = kwargs.get('_from', '')
        self._to = kwargs.get('_to', '')

    def to_json(self):
        return {
                'id': self.id,
                '_id': self._id,
                '_from': self._from,
                '_to': self._to
                 }


def conn(data):
    return Connection(**data)
