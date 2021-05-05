from modules.database import database
from models.Pipeline import pipeline


collection = 'pipeline'


def select(id):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1'
    items = database.select(collection, search, value=value)
    if len(items) == 0:
        return None
    return pipeline(items[0]) if not items[0] is None else None


def select_pipeline(**kwargs):

    search = 'FILTER '
    count = 0
    for key, value in kwargs.items():
        count = count + 1
        search = search + 'doc.' + key + ' == @' + key
        if count != len(kwargs.items()):
            search = search + " && "

    items = database.select(collection, search, **kwargs)
    if len(items) == 0:
        return None
    return [pipeline(item).to_json() for item in items]


def select_pipeline_edge(_key):
    items = database.select_edge(collection='pipeline', inboud=False, _key=_key)
    if len(items) == 0:
        return []
    return [pipeline(item).to_json() for item in items]


def update(id, data=None):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1 '

    items = database.update(collection, data, search, value=value)
    if len(items) == 0:
        return None
    return pipeline(items[0]) if not items[0] is None else None


def delete(id):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1 '
    items = database.delete(collection, search, value=value)
    if len(items) == 0:
        return None
    return pipeline(items[0]) if not items[0] is None else None


def insert(data):
    item = database.insert(collection, data)
    return pipeline(item['new'])


def count():
    arr = database.count(collection, '')
    return arr[0]


def createPipeline(body, job):
    arrRes = []
    return arrRes
