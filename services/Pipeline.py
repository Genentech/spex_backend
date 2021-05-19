from modules.database import database
from models.Pipeline import pipeline


collection = 'pipeline_direction'


def select(id, collection='pipeline_direction', toJson=False):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1'
    items = database.select(collection, search, value=value)
    if len(items) == 0:
        return None
    if toJson is True:
        return pipeline(items[0]).to_json() if not items[0] is None else None
    return pipeline(items[0]) if not items[0] is None else None


def select_pipeline(condition=None, collection='pipeline_direction', one=False, **kwargs):

    search = 'FILTER '
    count = 0
    for key, value in kwargs.items():
        count = count + 1
        search = search + 'doc.' + key + ' == @' + key
        if count != len(kwargs.items()):
            search = search + " && "
    if condition is not None:
        search = search.replace('==',  condition)

    items = database.select(collection, search, **kwargs)
    if len(items) == 0:
        return None
    if one is True:
        return pipeline(items[0]).to_json()
    return [pipeline(item).to_json() for item in items]


def select_pipeline_edge(_key):
    items = database.select_edge(collection='pipeline_direction', inboud=False, _key=_key)
    if len(items) == 0:
        return []
    if len(items) == 1:
        return pipeline(items[0]).to_json()
    return [pipeline(item).to_json() for item in items]


def update(id, data=None, collection='pipeline_direction'):
    value = id
    search = 'FILTER doc._key == @value LIMIT 1 '

    items = database.update(collection, data, search, value=value)
    if len(items) == 0:
        return None
    return pipeline(items[0]) if not items[0] is None else None


def delete(condition=None, collection='pipeline_direction', **kwargs):
    search = 'FILTER '
    count = 0
    for key, value in kwargs.items():
        count = count + 1
        search = search + 'doc.' + key + ' == @' + key
        if count != len(kwargs.items()):
            search = search + " && "
    if condition is not None:
        search = search.replace('==',  condition)
    items = database.delete(collection, search, **kwargs)
    if len(items) == 0:
        return None
    return pipeline(items[0]) if not items[0] is None else None


def insert(data, collection='pipeline_direction'):
    item = database.insert(collection, data)
    return pipeline(item['new'])


def count():
    arr = database.count(collection, '')
    return arr[0]


def createPipeline(body, job):
    arrRes = []
    return arrRes
