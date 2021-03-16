

class Job:
    def __init__(self, **kwargs):
        self.id = kwargs.get('_key', None)
        self.job = kwargs.get('job', '')

    def to_json(self):
        return {
            'id': self.id,
            'job': self.job,
        }


def job(data):
    return Job(**data)
